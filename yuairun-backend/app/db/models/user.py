"""User ORM 模型"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, SmallInteger

from app.db.session import Base


class UserModel(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, comment="用户唯一ID，格式 u_xxx")
    openid = Column(String(128), nullable=False, unique=True, comment="微信 openid")
    unionid = Column(String(128), nullable=True, default=None, comment="微信 unionid")
    nickname = Column(String(64), nullable=False, default="", comment="微信昵称")
    avatar_url = Column(String(512), nullable=False, default="", comment="微信头像 URL")
    xp = Column(Integer, nullable=False, default=0, comment="经验值")
    level = Column(Integer, nullable=False, default=1, comment="等级")
    last_login_at = Column(DateTime, nullable=True, default=None, comment="最后登录时间")
    is_deleted = Column(SmallInteger, nullable=False, default=0, comment="软删除标记")
    created_at = Column(DateTime, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, comment="更新时间")
    # 🆕 手动登录字段
    username = Column(String(64), nullable=True, unique=True, comment="登录用户名")
    password_hash = Column(String(256), nullable=True, comment="bcrypt 密码哈希")

    def to_dict(self) -> dict:
        """转为字典"""
        return {
            "id": self.id,
            "openid": self.openid,
            "unionid": self.unionid,
            "nickname": self.nickname,
            "avatarUrl": self.avatar_url,
            "xp": self.xp,
            "level": self.level,
            "lastLoginAt": self.last_login_at.isoformat() if self.last_login_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

    def update_login_time(self):
        """更新最后登录时间"""
        self.last_login_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)
