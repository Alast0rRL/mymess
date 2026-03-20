from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'text', 'link', 'file'
    content = db.Column(db.Text, nullable=False)  # Текст поста или URL
    file_path = db.Column(db.String(255), nullable=True)  # Путь к файлу для типа 'file'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Post {self.id}: {self.type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
