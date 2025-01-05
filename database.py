# database.py
import sqlite3
from datetime import datetime
from config import DB_PATH


class Database:
    def __init__(self):
        """初始化数据库连接"""
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """创建数据库表"""
        # 创建工地信息表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS construction_sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_name TEXT NOT NULL,
                manager_name TEXT,
                manager_phone TEXT
            )
        ''')

        # 创建检测记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                detection_time TIMESTAMP,
                total_people INTEGER,
                with_helmet INTEGER,
                without_helmet INTEGER,
                image_path TEXT,
                FOREIGN KEY (site_id) REFERENCES construction_sites(id)
            )
        ''')
        self.conn.commit()

    def add_site(self, site_name, manager_name, manager_phone):
        """添加新工地"""
        sql = "INSERT INTO construction_sites (site_name, manager_name, manager_phone) VALUES (?, ?, ?)"
        self.cursor.execute(sql, (site_name, manager_name, manager_phone))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_site(self, site_id, site_name, manager_name, manager_phone):
        """更新工地信息"""
        sql = """
            UPDATE construction_sites 
            SET site_name = ?, manager_name = ?, manager_phone = ?
            WHERE id = ?
        """
        self.cursor.execute(sql, (site_name, manager_name, manager_phone, site_id))
        self.conn.commit()

    def delete_site(self, site_id):
        """删除工地信息"""
        # 首先删除相关的检测记录
        self.cursor.execute("DELETE FROM detection_records WHERE site_id = ?", (site_id,))
        # 然后删除工地信息
        self.cursor.execute("DELETE FROM construction_sites WHERE id = ?", (site_id,))
        self.conn.commit()

    def get_sites(self):
        """获取所有工地信息"""
        self.cursor.execute("SELECT * FROM construction_sites ORDER BY site_name")
        return self.cursor.fetchall()

    def get_site_by_id(self, site_id):
        """根据ID获取工地信息"""
        self.cursor.execute("SELECT * FROM construction_sites WHERE id = ?", (site_id,))
        return self.cursor.fetchone()

    def get_site_by_name(self, site_name):
        """根据名称获取工地信息"""
        self.cursor.execute("SELECT * FROM construction_sites WHERE site_name = ?", (site_name,))
        return self.cursor.fetchone()

    def add_detection_record(self, site_id, total_people, with_helmet, without_helmet, image_path):
        """添加检测记录"""
        sql = """
            INSERT INTO detection_records 
            (site_id, detection_time, total_people, with_helmet, without_helmet, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(sql, (
            site_id,
            datetime.now(),
            total_people,
            with_helmet,
            without_helmet,
            image_path
        ))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_record(self, record_id, site_id, total_people, with_helmet, without_helmet):
        """更新检测记录"""
        sql = """
            UPDATE detection_records 
            SET site_id = ?, total_people = ?, with_helmet = ?, without_helmet = ?
            WHERE id = ?
        """
        self.cursor.execute(sql, (site_id, total_people, with_helmet, without_helmet, record_id))
        self.conn.commit()

    def delete_record(self, record_id):
        """删除检测记录"""
        # 获取图片路径用于删除文件
        self.cursor.execute("SELECT image_path FROM detection_records WHERE id = ?", (record_id,))
        result = self.cursor.fetchone()
        image_path = result[0] if result else None

        # 删除记录
        self.cursor.execute("DELETE FROM detection_records WHERE id = ?", (record_id,))
        self.conn.commit()

        return image_path

    def get_records(self, site_id=None, start_date=None, end_date=None):
        """获取检测记录"""
        sql = "SELECT * FROM detection_records WHERE 1=1"
        params = []

        if site_id:
            sql += " AND site_id = ?"
            params.append(site_id)
        if start_date:
            sql += " AND date(detection_time) >= ?"
            params.append(str(start_date))
        if end_date:
            sql += " AND date(detection_time) <= ?"
            params.append(str(end_date))

        sql += " ORDER BY detection_time DESC"

        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def get_records_with_site_name(self, site_name=None, start_date=None, end_date=None):
        """支持按工地名称模糊查询的记录获取方法"""
        sql = """
            SELECT 
                dr.id,
                dr.site_id,
                dr.detection_time,
                dr.total_people,
                dr.with_helmet,
                dr.without_helmet,
                dr.image_path,
                cs.site_name,
                cs.manager_name,
                cs.manager_phone
            FROM detection_records dr
            JOIN construction_sites cs ON dr.site_id = cs.id
            WHERE 1=1
        """
        params = []

        if site_name:
            sql += " AND cs.site_name LIKE ?"
            params.append(f'%{site_name}%')
        if start_date:
            sql += " AND date(dr.detection_time) >= ?"
            params.append(str(start_date))
        if end_date:
            sql += " AND date(dr.detection_time) <= ?"
            params.append(str(end_date))

        sql += " ORDER BY dr.detection_time DESC"

        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def get_low_compliance_sites(self, threshold=0.8):
        """获取安全帽佩戴率低于阈值的工地"""
        sql = """
            SELECT 
                cs.site_name,
                cs.manager_name,
                cs.manager_phone,
                COUNT(*) as total_records,
                AVG(CAST(dr.with_helmet AS FLOAT) / CAST(dr.total_people AS FLOAT)) as compliance_rate
            FROM detection_records dr
            JOIN construction_sites cs ON dr.site_id = cs.id
            GROUP BY cs.id
            HAVING compliance_rate < ?
            ORDER BY compliance_rate ASC
        """
        self.cursor.execute(sql, (threshold,))
        return self.cursor.fetchall()

    def get_site_statistics(self, site_id, days=30):
        """获取指定工地的统计数据"""
        sql = """
            SELECT 
                date(detection_time) as date,
                COUNT(*) as detection_count,
                AVG(CAST(with_helmet AS FLOAT) / CAST(total_people AS FLOAT)) as avg_compliance_rate,
                SUM(total_people) as total_people,
                SUM(with_helmet) as total_with_helmet,
                SUM(without_helmet) as total_without_helmet
            FROM detection_records
            WHERE site_id = ? AND detection_time >= date('now', ?)
            GROUP BY date(detection_time)
            ORDER BY date ASC
        """
        self.cursor.execute(sql, (site_id, f'-{days} days'))
        return self.cursor.fetchall()

    def __del__(self):
        """析构函数，确保关闭数据库连接"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()