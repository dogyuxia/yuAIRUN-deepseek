开发RAG中Bug如下







1）现象：输入新知识库名称时默认‘请输入知识库名称’没有删除，我打开输入框还有手动删除

预期：输入时可以自动删除



![image-20260624192702222](C:\Users\31611\AppData\Roaming\Typora\typora-user-images\image-20260624192702222.png)

2)现象：创建新知识库‘八股文’失败，显示创建失败但是在AI出题时有可以选择但是没有分块如图

后端请求如下；

1. {id: "kb_8d1e8c078faf", name: "八股文", description: "", isSystem: false, docCount: 0, chunkCount: 0,…}

2. 1. chunkCount: 0
   2. createdAt: "2026-06-24T11:28:55"
   3. description: ""
   4. docCount: 0
   5. id: "kb_8d1e8c078faf"
   6. isSystem: false
   7. name: "八股文"
   8. updatedAt: "2026-06-24T11:28:55"![image-20260624193339019](C:\Users\31611\AppData\Roaming\Typora\typora-user-images\image-20260624193339019.png)

3）现象：点击上传文件按钮没有反应如图

![image-20260624193652710](C:\Users\31611\AppData\Roaming\Typora\typora-user-images\image-20260624193652710.png)



4）现象：默认知识库中文件少了，小程序中只显示了六个
![image-20260624193751287](C:\Users\31611\AppData\Roaming\Typora\typora-user-images\image-20260624193751287.png)

5）现象：使用知识库生成题目时候显示：知识库中没有足够的相关内容，请尝试其他知识库或使用AI搜索模式

但是如图我选择的是仅知识库，计算机学科，知识点是memory，为啥没有相关内容 ，按理说应该应该有知识点，没有读取到知识库吗



![image-20260624193920394](C:\Users\31611\AppData\Roaming\Typora\typora-user-images\image-20260624193920394.png)

6）现象：AI分析报告生成失败后点击重新生成，一段时间后后端返回的analyze正确但是页面没有刷新到AI分析界面，一直停留在生成失败界面如图

![image-20260624194649956](C:\Users\31611\AppData\Roaming\Typora\typora-user-images\image-20260624194649956.png)



