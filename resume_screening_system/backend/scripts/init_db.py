from app.core.database import bootstrap_schema


if __name__ == "__main__":
    bootstrap_schema()
    print("数据库结构初始化完成。")
