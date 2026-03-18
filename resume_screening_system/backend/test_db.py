from app.core.database import engine

try:
    with engine.connect() as conn:
        print("数据库连接成功")
except Exception as e:
    print("数据库连接失败")
    print(e)