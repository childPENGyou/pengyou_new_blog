# coding:utf-8

from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship, backref

DbBase = declarative_base()


class DbInit():
    created_at = Column(DateTime, default=datetime.utcnow)


class User(DbBase, DbInit):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(64), unique=True, index=True)
    username = Column(String(64), unique=True, index=True)
    password = Column(String(128))

    def verify_password(self, password):
        return self.password == password


class Menu(DbBase):
    __tablename__ = 'menus'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    types = relationship('ArticleType', backref='menu', lazy='dynamic')
    order = Column(Integer, default=0, nullable=False)

    def sort_delete(self, session):
        for menu in Menu.query.order_by(Menu.order).offset(self.order).all():
            menu.order -= 1
            session.add(menu)
        session.commit()

    @staticmethod
    def return_menus():
        menus = [(m.id, m.name) for m in Menu.query.all()]
        menus.append((-1, u'不选择导航（该分类将单独成一导航）'))
        return menus

    def __repr__(self):
        return '<Menu %r>' % self.name


class ArticleTypeSetting(DbBase):
    __tablename__ = 'articleTypeSettings'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    protected = Column(Boolean, default=False)
    hide = Column(Boolean, default=False)
    types = relationship('ArticleType', backref='setting', lazy='dynamic')

    @staticmethod
    def return_setting_hide():
        return [(2, u'公开'), (1, u'隐藏')]

    def __repr__(self):
        return '<ArticleTypeSetting %r>' % self.name


class ArticleType(DbBase):
    __tablename__ = 'articleTypes'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    introduction = Column(Text, default=None)
    articles = relationship('Article', backref='articleType', lazy='dynamic')
    menu_id = Column(Integer, ForeignKey('menus.id'), default=None)
    setting_id = Column(Integer, ForeignKey('articleTypeSettings.id'))

    @property
    def is_protected(self):
        if self.setting:
            return self.setting.protected
        else:
            return False

    @property
    def is_hide(self):
        if self.setting:
            return self.setting.hide
        else:
            return False

    # if the articleType does not have setting,
    # its is_hie and is_protected property will be False.

    def __repr__(self):
        return '<Type %r>' % self.name


class Source(DbBase):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    articles = relationship('Article', backref='source', lazy='dynamic')

    def __repr__(self):
        return '<Source %r>' % self.name


class Follow(DbBase):
    __tablename__ = 'follows'

    # folloer_id和followed_id 共同组成了一个复合主键
    follower_id = Column(Integer, ForeignKey('comments.id'), primary_key=True)
    followed_id = Column(Integer, ForeignKey('comments.id'), primary_key=True)


class Comment(DbBase):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    author_name = Column(String(64))
    author_email = Column(String(64))
    article_id = Column(Integer, ForeignKey('articles.id'))
    disabled = Column(String(128), default=False)
    comment_type = Column(String(64), default='comment')
    reply_to = Column(String(128), default='notReply')
    followed = relationship('Follow',
                            foreign_keys=[Follow.follower_id],
                            backref=backref('follower', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')
    followers = relationship('Follow',
                             foreign_keys=[Follow.followed_id],
                             backref=backref('followed', lazy='joined'),
                             lazy='dynamic',
                             cascade='all, delete-orphan')

    def is_reply(self):
        if self.followed.count() == 0:
            return False
        else:
            return True


