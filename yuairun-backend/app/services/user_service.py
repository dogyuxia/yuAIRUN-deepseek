"""用户系统业务逻辑层"""

import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.auth import create_token, hash_password, verify_password
from app.db.models.user import UserModel
from app.db.models.quiz_history import QuizHistoryModel
from app.db.models.quiz_answer import QuizAnswerModel
from app.db.models.wrong_book import WrongBookModel


# ============================================================
# XP / 等级 / 称号 常量与计算
# ============================================================

LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 2000]
LEVEL_TITLES = ["", "初学者", "学徒", "探究者", "学者", "大师", "传奇"]

XP_PER_CORRECT = 10          # 答对一题
XP_STREAK_BONUS = 5          # 连续答题额外奖励/题
XP_FIRST_QUIZ = 50           # 首次完成闯关
XP_PERFECT_BONUS = 20        # 100%正确额外奖励


def calculate_level(xp: int) -> int:
    """根据 XP 计算等级"""
    for level, threshold in enumerate(LEVEL_THRESHOLDS, 1):
        if xp < threshold:
            return level - 1
    return len(LEVEL_THRESHOLDS)


def get_level_title(level: int) -> str:
    """根据等级获取称号"""
    if level < len(LEVEL_TITLES):
        return LEVEL_TITLES[level]
    return "传奇"


def get_next_level_xp(level: int) -> int:
    """获取下一级所需 XP"""
    if level < len(LEVEL_THRESHOLDS):
        return LEVEL_THRESHOLDS[level]
    return LEVEL_THRESHOLDS[-1] + 1000 * (level - len(LEVEL_THRESHOLDS) + 1)


def generate_id(prefix: str = "u") -> str:
    """生成唯一 ID 如 u_xxx / h_xxx / qa_xxx / wb_xxx"""
    unique = hashlib.md5(f"{uuid.uuid4().hex}{datetime.now().timestamp()}".encode()).hexdigest()[:12]
    return f"{prefix}_{unique}"


# ============================================================
# XP 计算
# ============================================================

def calculate_xp_earned(correct_count: int, total_count: int, is_first_quiz: bool) -> int:
    """计算本次闯关获得的经验值"""
    xp = correct_count * XP_PER_CORRECT

    # 连续答题奖励（第2题起额外 +5 XP）
    if correct_count >= 2:
        xp += (correct_count - 1) * XP_STREAK_BONUS

    # 首次完成闯关额外奖励
    if is_first_quiz:
        xp += XP_FIRST_QUIZ

    # 100%正确额外奖励
    if correct_count == total_count and total_count > 0:
        xp += XP_PERFECT_BONUS

    return xp


# ============================================================
# 用户登录/注册
# ============================================================

async def login_or_register(
    db: AsyncSession,
    code: str,
    nickname: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> dict:
    """
    微信登录/注册

    模拟阶段：将 code 作为 openid 使用
    """
    openid = code  # 模拟阶段：code 直接作为 openid

    # 查找用户
    result = await db.execute(select(UserModel).where(UserModel.openid == openid))
    user = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    is_new_user = False

    if user is None:
        # 新用户注册
        user = UserModel(
            id=generate_id("u"),
            openid=openid,
            nickname=nickname or f"用户_{openid[-6:]}",
            avatar_url=avatar_url or "",
            xp=0,
            level=1,
            last_login_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        is_new_user = True
    else:
        # 已有用户：更新最后登录时间和信息
        user.update_login_time()
        if nickname:
            user.nickname = nickname
        if avatar_url:
            user.avatar_url = avatar_url

    await db.commit()
    await db.refresh(user)

    # 签发 JWT
    token, expires_in = create_token(user.id, user.openid)

    return {
        "token": token,
        "expiresIn": expires_in,
        "user": {
            "id": user.id,
            "nickname": user.nickname,
            "avatarUrl": user.avatar_url,
            "xp": user.xp,
            "level": user.level,
            "levelTitle": get_level_title(user.level),
            "isNewUser": is_new_user,
        },
    }


# ============================================================
# 手动登录/注册
# ============================================================

async def manual_login_or_register(
    db: AsyncSession,
    username: str,
    password: str,
) -> dict:
    """
    用户名密码登录/自动注册

    1. 查 username 是否已存在
    2. 存在 → 校验密码
    3. 不存在 → 自动注册新用户
    """
    now = datetime.now(timezone.utc)
    openid = f"manual_{username}"  # 手动登录用户使用特殊 openid 前缀

    result = await db.execute(select(UserModel).where(UserModel.username == username))
    user = result.scalar_one_or_none()

    if user:
        # 已存在 → 校验密码
        if not verify_password(password, user.password_hash or ""):
            raise ValueError("密码错误")
        user.update_login_time()
    else:
        # 不存在 → 自动注册
        user = UserModel(
            id=generate_id("u"),
            openid=openid,
            username=username,
            nickname=username,
            password_hash=hash_password(password),
            xp=0,
            level=1,
            last_login_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # 签发 JWT
    token, expires_in = create_token(user.id, user.openid)

    return {
        "token": token,
        "expiresIn": expires_in,
        "user": {
            "id": user.id,
            "nickname": user.nickname,
            "avatarUrl": user.avatar_url,
            "xp": user.xp,
            "level": user.level,
            "levelTitle": get_level_title(user.level),
            "isNewUser": user.username == username and user.xp == 0,
        },
    }


# ============================================================
# 用户信息
# ============================================================

async def get_user_profile(db: AsyncSession, user_id: str) -> dict:
    """获取用户详细信息和统计"""
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("用户不存在")

    # 聚合统计
    stats_result = await db.execute(
        select(
            func.count(QuizHistoryModel.id).label("total_quizzes"),
            func.coalesce(func.sum(QuizHistoryModel.question_count), 0).label("total_questions"),
            func.coalesce(func.sum(QuizHistoryModel.correct_count), 0).label("total_correct"),
            func.coalesce(func.sum(QuizHistoryModel.duration), 0).label("total_duration"),
        ).where(QuizHistoryModel.user_id == user_id)
    )
    stats_row = stats_result.one()

    total_quizzes = stats_row.total_quizzes or 0
    total_questions = stats_row.total_questions or 0
    total_correct = stats_row.total_correct or 0
    total_wrong = total_questions - total_correct
    total_duration = stats_row.total_duration or 0
    accuracy = round(total_correct / total_questions, 4) if total_questions > 0 else 0

    # 最近活跃日期
    last_active = await db.execute(
        select(QuizHistoryModel.created_at)
        .where(QuizHistoryModel.user_id == user_id)
        .order_by(desc(QuizHistoryModel.created_at))
        .limit(1)
    )
    last_active_row = last_active.scalar_one_or_none()

    # 连续学习天数（简化：从最近记录日期往前推断）
    streak_days = await _calculate_streak_days(db, user_id)

    last_active_date = None
    if last_active_row:
        last_active_date = last_active_row.strftime("%Y-%m-%d")

    # 最近5条闯关记录
    recent_result = await db.execute(
        select(QuizHistoryModel)
        .where(QuizHistoryModel.user_id == user_id)
        .order_by(desc(QuizHistoryModel.created_at))
        .limit(5)
    )
    recent_histories = [h.to_dict() for h in recent_result.scalars().all()]

    level = user.level
    next_level_xp = get_next_level_xp(level)

    return {
        "id": user.id,
        "nickname": user.nickname,
        "avatarUrl": user.avatar_url,
        "xp": user.xp,
        "level": level,
        "levelTitle": get_level_title(level),
        "nextLevelXp": next_level_xp,
        "stats": {
            "totalQuizzes": total_quizzes,
            "totalQuestions": total_questions,
            "totalCorrect": total_correct,
            "totalWrong": total_wrong,
            "accuracy": accuracy,
            "totalDuration": total_duration,
            "streakDays": streak_days,
            "lastActiveDate": last_active_date,
        },
        "recentHistories": recent_histories,
    }


async def update_user_profile(db: AsyncSession, user_id: str, nickname: Optional[str] = None) -> dict:
    """更新用户信息"""
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("用户不存在")

    if nickname is not None:
        if not nickname.strip():
            raise ValueError("昵称不能为空")
        user.nickname = nickname.strip()

    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "nickname": user.nickname,
        "avatarUrl": user.avatar_url,
        "xp": user.xp,
        "level": user.level,
        "levelTitle": get_level_title(user.level),
    }


# ============================================================
# 闯关历史
# ============================================================

async def get_history_list(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """分页获取闯关历史"""
    offset = (page - 1) * page_size

    # 总数
    count_result = await db.execute(
        select(func.count(QuizHistoryModel.id))
        .where(QuizHistoryModel.user_id == user_id)
    )
    total = count_result.scalar() or 0

    # 列表
    result = await db.execute(
        select(QuizHistoryModel)
        .where(QuizHistoryModel.user_id == user_id)
        .order_by(desc(QuizHistoryModel.created_at))
        .offset(offset)
        .limit(page_size)
    )
    items = [h.to_dict() for h in result.scalars().all()]

    return {
        "items": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "hasMore": (offset + page_size) < total,
    }


async def get_history_detail(db: AsyncSession, user_id: str, history_id: str) -> dict:
    """获取单条闯关记录详情"""
    result = await db.execute(
        select(QuizHistoryModel)
        .where(QuizHistoryModel.id == history_id, QuizHistoryModel.user_id == user_id)
    )
    history = result.scalar_one_or_none()
    if not history:
        raise ValueError("闯关记录不存在")

    # 获取答题详情
    answers_result = await db.execute(
        select(QuizAnswerModel)
        .where(QuizAnswerModel.history_id == history_id)
        .order_by(QuizAnswerModel.created_at)
    )
    answers = [a.to_dict() for a in answers_result.scalars().all()]

    data = history.to_dict()
    data["answers"] = answers
    return data


async def sync_history_records(
    db: AsyncSession,
    user_id: str,
    records: list,
) -> dict:
    """批量同步闯关记录到服务端"""
    now = datetime.now(timezone.utc)
    synced_count = 0
    total_count = 0
    total_xp_earned = 0

    # 检查用户是否已有闯关记录（用于判断是否"首次"）
    existing_count = await db.execute(
        select(func.count(QuizHistoryModel.id))
        .where(QuizHistoryModel.user_id == user_id)
    )
    existing_total = existing_count.scalar() or 0

    for record in records:
        total_count += 1
        is_first_quiz = (existing_total + synced_count) == 0

        # 计算 XP
        xp_earned = calculate_xp_earned(
            record.get("correctCount", 0),
            record.get("totalCount", 0),
            is_first_quiz,
        )
        total_xp_earned += xp_earned

        # 解析时间
        try:
            created_at = datetime.fromisoformat(record["createdAt"])
        except (ValueError, KeyError):
            created_at = now

        # 创建闯关历史记录
        history = QuizHistoryModel(
            id=generate_id("h"),
            user_id=user_id,
            subject=record.get("subject", ""),
            topic=record.get("topic", ""),
            question_count=record.get("totalCount", 0),
            correct_count=record.get("correctCount", 0),
            accuracy=record.get("accuracy", 0),
            duration=record.get("duration", 0),
            xp_earned=xp_earned,
            created_at=created_at,
        )
        db.add(history)
        await db.flush()
        synced_count += 1

        # 写入答题详情
        questions = record.get("questions", [])
        user_answers = record.get("userAnswers", {})

        for q in questions:
            q_id = q.get("id", "")
            user_ans = user_answers.get(q_id, "")

            # 判断对错
            correct_ans = q.get("answer", "")
            if isinstance(correct_ans, list):
                is_correct = isinstance(user_ans, list) and sorted(user_ans) == sorted(correct_ans)
            else:
                is_correct = str(user_ans) == str(correct_ans)

            answer = QuizAnswerModel(
                id=generate_id("qa"),
                history_id=history.id,
                user_id=user_id,
                question=q,
                user_answer=str(user_ans) if not isinstance(user_ans, list) else ",".join(user_ans),
                is_correct=1 if is_correct else 0,
                created_at=created_at,
            )
            db.add(answer)

            # 答错的题目自动写入错题本
            if not is_correct:
                await _upsert_wrong_book(
                    db, user_id, history.id, q,
                    str(user_ans) if not isinstance(user_ans, list) else ",".join(user_ans),
                    str(correct_ans) if not isinstance(correct_ans, list) else ",".join(correct_ans),
                    record.get("subject", ""),
                    record.get("topic", ""),
                    created_at,
                )

    # 更新用户 XP 和等级
    user_result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = user_result.scalar_one_or_none()
    if user:
        user.xp += total_xp_earned
        user.level = calculate_level(user.xp)
        user.updated_at = now

    await db.commit()

    return {
        "syncedCount": synced_count,
        "totalCount": total_count,
        "xpEarned": total_xp_earned,
        "currentXp": user.xp if user else 0,
        "currentLevel": user.level if user else 1,
    }


# ============================================================
# 错题本
# ============================================================

async def get_wrong_book(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    subject: Optional[str] = None,
) -> dict:
    """分页获取错题本"""
    offset = (page - 1) * page_size

    # 构建查询
    query = select(WrongBookModel).where(
        WrongBookModel.user_id == user_id,
        WrongBookModel.is_mastered == 0,
    )
    count_query = select(func.count(WrongBookModel.id)).where(
        WrongBookModel.user_id == user_id,
        WrongBookModel.is_mastered == 0,
    )

    if subject:
        query = query.where(WrongBookModel.subject == subject)
        count_query = count_query.where(WrongBookModel.subject == subject)

    # 总数
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # 列表
    result = await db.execute(
        query.order_by(desc(WrongBookModel.last_wrong_at))
        .offset(offset)
        .limit(page_size)
    )
    items = [w.to_dict() for w in result.scalars().all()]

    return {
        "items": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "hasMore": (offset + page_size) < total,
    }


async def sync_wrong_book(db: AsyncSession, user_id: str, items: list) -> dict:
    """批量同步错题"""
    now = datetime.now(timezone.utc)
    synced_count = 0

    for item in items:
        question = item.get("question", {})
        user_answer = item.get("userAnswer", "")
        correct_answer = item.get("correctAnswer", "")
        subject = item.get("subject", "")
        topic = item.get("topic", "")

        # 检查是否已存在相同错题
        existing = await db.execute(
            select(WrongBookModel).where(
                WrongBookModel.user_id == user_id,
                WrongBookModel.subject == subject,
                WrongBookModel.correct_answer == correct_answer,
                WrongBookModel.is_mastered == 0,
            ).limit(1)
        )
        existing_item = existing.scalar_one_or_none()

        if existing_item:
            # 累加错误次数
            existing_item.wrong_count += 1
            existing_item.last_wrong_at = now
            existing_item.updated_at = now
        else:
            # 新建错题记录（使用一个虚拟 history_id）
            wrong = WrongBookModel(
                id=generate_id("wb"),
                user_id=user_id,
                history_id="pending",
                question=question,
                user_answer=user_answer,
                correct_answer=correct_answer,
                subject=subject,
                topic=topic,
                wrong_count=1,
                last_wrong_at=now,
                created_at=now,
                updated_at=now,
            )
            db.add(wrong)

        synced_count += 1

    await db.commit()
    return {"syncedCount": synced_count}


async def mark_wrong_book_mastered(db: AsyncSession, user_id: str, wrong_id: str) -> dict:
    """标记错题为已掌握"""
    result = await db.execute(
        select(WrongBookModel)
        .where(WrongBookModel.id == wrong_id, WrongBookModel.user_id == user_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise ValueError("错题记录不存在")

    item.is_mastered = 1
    item.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "已标记为已掌握"}


async def delete_wrong_book(db: AsyncSession, user_id: str, wrong_id: str) -> dict:
    """从错题本删除"""
    result = await db.execute(
        select(WrongBookModel)
        .where(WrongBookModel.id == wrong_id, WrongBookModel.user_id == user_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise ValueError("错题记录不存在")

    await db.delete(item)
    await db.commit()

    return {"message": "已删除"}


# ============================================================
# 内部辅助方法
# ============================================================

async def _upsert_wrong_book(
    db: AsyncSession,
    user_id: str,
    history_id: str,
    question: dict,
    user_answer: str,
    correct_answer: str,
    subject: str,
    topic: str,
    created_at: datetime,
):
    """插入或更新错题本"""
    # 检查是否已存在相同题目
    result = await db.execute(
        select(WrongBookModel).where(
            WrongBookModel.user_id == user_id,
            WrongBookModel.correct_answer == correct_answer,
            WrongBookModel.is_mastered == 0,
        ).limit(1)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.wrong_count += 1
        existing.last_wrong_at = created_at
        existing.updated_at = created_at
    else:
        wrong = WrongBookModel(
            id=generate_id("wb"),
            user_id=user_id,
            history_id=history_id,
            question=question,
            user_answer=user_answer,
            correct_answer=correct_answer,
            subject=subject,
            topic=topic,
            wrong_count=1,
            last_wrong_at=created_at,
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(wrong)


async def _calculate_streak_days(db: AsyncSession, user_id: str) -> int:
    """计算连续学习天数"""
    result = await db.execute(
        select(QuizHistoryModel.created_at)
        .where(QuizHistoryModel.user_id == user_id)
        .order_by(desc(QuizHistoryModel.created_at))
    )
    dates = [row[0].date() for row in result.fetchall()]

    if not dates:
        return 0

    # 去重
    unique_dates = []
    for d in dates:
        if not unique_dates or d != unique_dates[-1]:
            unique_dates.append(d)

    # 计算连续天数
    streak = 0
    today = datetime.now(timezone.utc).date()

    for i, d in enumerate(unique_dates):
        expected = today - timedelta(days=i)
        if d == expected:
            streak += 1
        else:
            break

    return streak
