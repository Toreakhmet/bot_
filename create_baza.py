import psycopg2
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

parms_for_postgresql = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT")
}

logger.info("СТАРТ СОЗДАНИЕ БАЗЫ ДАННЫХ")

try:
    with psycopg2.connect(**parms_for_postgresql) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            logger.info(f"Версия PostgreSQL: {db_version}")

            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS users (
                                id BIGINT PRIMARY KEY,
                                name VARCHAR(100),
                                telegram_id VARCHAR(100),
                                iin VARCHAR(20),
                                fio VARCHAR(40),
                                date_of_birth DATE,
                                date_of_issue DATE,
                                issued_by VARCHAR(100)
                            );
                        """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id BIGINT PRIMARY KEY,
                    name VARCHAR(100),
                    telegram_id VARCHAR(100),
                    admin BOOLEAN
                );
            """)

            connection.commit()
            logger.info("БАЗА ДАННЫХ СОЗДАНА")

except Exception as error:
    logger.error(f"Ошибка при подключении к PostgreSQL: {error}")
