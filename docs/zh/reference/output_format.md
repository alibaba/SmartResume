# 输出格式

## JSON 格式

```json
{
  "resume_id": "resume_001",
  "basic_info": {
    "name": "张三",
    "phone": "13800138000",
    "email": "zhangsan@example.com"
  },
  "work_experience": [
    {
      "company": "ABC公司",
      "position": "软件工程师",
      "duration": "2020-2023"
    }
  ]
}
```

## CSV 格式

```csv
resume_id,name,phone,email,company,position
resume_001,张三,13800138000,zhangsan@example.com,ABC公司,软件工程师
```

## XML 格式

```xml
<resume id="resume_001">
  <basic_info>
    <name>张三</name>
    <phone>13800138000</phone>
    <email>zhangsan@example.com</email>
  </basic_info>
</resume>
```

## 下一步

- [查看基准测试](benchmark.md)
- [了解常见问题](faq.md)

