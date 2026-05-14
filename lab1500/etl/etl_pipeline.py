import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, text
import logging
import sys
import os

os.makedirs('logs', exist_ok=True)
os.makedirs('report/graphs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SalesETLPipeline:
    def __init__(self, csv_path: str, db_path: str = 'sales.db'):
        self.csv_path = csv_path
        self.db_path = db_path
        self.raw_data = None
        self.cleaned_data = None
        self.aggregated_data = None

    def extract(self) -> pd.DataFrame:
        logger.info("=" * 50)
        logger.info("НАЧАЛО ЭТАПА EXTRACT")

        try:
            try:
                self.raw_data = pd.read_csv(self.csv_path, encoding='utf-8')
            except UnicodeDecodeError:
                logger.info("UTF-8 не подошёл, пробуем windows-1251")
                self.raw_data = pd.read_csv(self.csv_path, encoding='windows-1251')

            if self.raw_data.empty:
                raise ValueError("CSV файл пуст")
        except FileNotFoundError:
            logger.error(f"Файл {self.csv_path} не найден")
            raise
        except Exception as e:
            logger.error(f"Ошибка чтения CSV: {e}")
            raise

        num_rows, num_cols = self.raw_data.shape
        logger.info(f"Загружено {num_rows} строк, {num_cols} колонок")
        logger.info(f"Колонки: {', '.join(self.raw_data.columns)}")
        logger.info("Типы данных:\n" + self.raw_data.dtypes.to_string())
        logger.info("Пропуски:\n" + self.raw_data.isnull().sum().to_string())
        return self.raw_data

    def transform(self) -> pd.DataFrame:
        logger.info("=" * 50)
        logger.info("НАЧАЛО ЭТАПА TRANSFORM")
        df = self.raw_data.copy()
        initial_rows = len(df)
        df.drop_duplicates(inplace=True)
        dup_removed = initial_rows - len(df)
        logger.info(f"Удалено дубликатов: {dup_removed}")

        numeric_cols = ['quantity', 'price_per_unit']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            median_val = df[col].median()
            null_count = df[col].isnull().sum()
            df[col] = df[col].fillna(median_val)
            logger.info(f"Колонка '{col}': NaN до обработки {null_count}, медиана {median_val:.2f}")

        text_cols = ['category', 'product_name', 'customer_name', 'customer_city', 'payment_method']
        for col in text_cols:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                df[col] = df[col].fillna('Unknown')
                logger.info(f"Колонка '{col}': пропусков {null_count}, заменены на 'Unknown'")

        before_filter = len(df)
        df = df[(df['quantity'] > 0) & (df['price_per_unit'] > 0)]
        removed_anomalies = before_filter - len(df)
        logger.info(f"Удалено строк с аномалиями: {removed_anomalies}")

        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        date_null = df['order_date'].isnull().sum()
        if date_null > 0:
            logger.warning(f"Удалено строк с некорректной датой: {date_null}")
            df.dropna(subset=['order_date'], inplace=True)

        df['quantity'] = df['quantity'].astype(int)
        df['price_per_unit'] = df['price_per_unit'].astype(float)

        df['total_amount'] = df['quantity'] * df['price_per_unit']
        df['month_year'] = df['order_date'].dt.strftime('%Y-%m')

        self.cleaned_data = df
        logger.info(f"После очистки: {len(df)} строк (удалено всего {initial_rows - len(df)})")
        logger.info(f"Диапазон дат: {df['order_date'].min().date()} – {df['order_date'].max().date()}")
        return self.cleaned_data

    def aggregate(self) -> pd.DataFrame:
        logger.info("=" * 50)
        logger.info("НАЧАЛО ЭТАПА AGGREGATE")

        df = self.cleaned_data.copy()
        self.aggregated_data = df.groupby(['category', 'month_year']).agg(
            total_quantity=('quantity', 'sum'),
            total_revenue=('total_amount', 'sum'),
            avg_price=('price_per_unit', 'mean'),
            order_count=('order_id', 'nunique')
        ).reset_index()

        self.aggregated_data['avg_price'] = self.aggregated_data['avg_price'].round(2)
        self.aggregated_data['total_revenue'] = self.aggregated_data['total_revenue'].round(2)
        logger.info(f"Агрегировано {len(self.aggregated_data)} групп")
        logger.info("\n" + self.aggregated_data.to_string())
        return self.aggregated_data

    def load_to_sqlite(self):
        logger.info("=" * 50)
        logger.info("НАЧАЛО ЭТАПА LOAD")

        engine = create_engine(f'sqlite:///{self.db_path}')

        self.cleaned_data.to_sql('sales_cleaned', engine, if_exists='replace', index=False)
        logger.info(f"Таблица 'sales_cleaned' сохранена ({len(self.cleaned_data)} записей)")

        self.aggregated_data.to_sql('sales_aggregated', engine, if_exists='replace', index=False)
        logger.info(f"Таблица 'sales_aggregated' сохранена ({len(self.aggregated_data)} записей)")

        with engine.connect() as conn:
            tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
            logger.info(f"Таблицы в БД: {[t[0] for t in tables]}")
            agg_data = conn.execute(text("SELECT * FROM sales_aggregated;")).fetchall()
            logger.info("Содержимое sales_aggregated:")
            for row in agg_data:
                logger.info(row)

        logger.info(f"Данные загружены в {self.db_path}")

    def visualize(self):
        logger.info("=" * 50)
        logger.info("НАЧАЛО ЭТАПА VISUALIZE")

        sns.set_style("whitegrid")

        cat_revenue = self.aggregated_data.groupby('category')['total_revenue'].sum().sort_values(ascending=False)
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=cat_revenue.index, y=cat_revenue.values, palette='viridis')
        plt.title('Выручка по категориям товаров', fontsize=16)
        plt.xlabel('Категория')
        plt.ylabel('Выручка (руб.)')
        for i, v in enumerate(cat_revenue.values):
            ax.text(i, v + 1000, f'{v:,.0f}', ha='center', fontweight='bold')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('graphs_png/1.png')
        plt.show()

        monthly = self.aggregated_data.groupby(['month_year', 'category'])['total_revenue'].sum().unstack(fill_value=0)
        plt.figure(figsize=(12, 6))
        monthly.plot(marker='o', linewidth=2.5, ax=plt.gca())
        plt.title('Динамика выручки по категориям (по месяцам)', fontsize=16)
        plt.xlabel('Месяц')
        plt.ylabel('Выручка (руб.)')
        plt.legend(title='Категория')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('graphs_png/2.png')
        plt.show()

        plt.figure(figsize=(8, 8))
        cat_total = self.aggregated_data.groupby('category')['total_revenue'].sum()
        plt.pie(cat_total, labels=cat_total.index, autopct='%1.1f%%', startangle=90,
                colors=sns.color_palette('pastel'), explode=(0.05, 0.05, 0.05))
        plt.title('Доля категорий в общей выручке', fontsize=16)
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig('graphs_png/3.png')
        plt.show()

        logger.info("Графики сохранены в graphs_png")

    def run(self):
        logger.info("=" * 50)
        logger.info("ЗАПУСК ETL ПАЙПЛАЙНА")
        logger.info("=" * 50)

        self.extract()
        self.transform()
        self.aggregate()
        self.load_to_sqlite()
        self.visualize()

        logger.info("=" * 50)
        logger.info("ETL ПАЙПЛАЙН УСПЕШНО ЗАВЕРШЁН")
        logger.info("=" * 50)


if __name__ == "__main__":
    pipeline = SalesETLPipeline('data/sales.csv', 'sales.db')
    pipeline.run()