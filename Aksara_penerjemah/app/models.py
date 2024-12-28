from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()



class Pengguna(UserMixin, db.Model):
    __tablename__ = 'pengguna'
    id_pengguna = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_pengguna = db.Column(db.String, unique=True, nullable=False)
    kata_sandi = db.Column(db.String, nullable=False)
    peran = db.Column(db.String)

    def get_id(self):
        return str(self.id_pengguna)

class Kata(db.Model):
    __tablename__ = 'kata'
    id_kata = db.Column(db.Integer, primary_key=True, autoincrement=True)
    konten = db.Column(db.Text)
    status_validasi = db.Column(db.Boolean, default=False)
    id_kelompok = db.Column(db.Integer, nullable=True, autoincrement=True)  # Menambahkan kolom id_kelompok yang tidak unique
    jenis_varian = db.Column(db.String, nullable=True)  # Menambahkan kolom jenis_varian
    created_by = db.Column(db.Integer, db.ForeignKey('pengguna.id_pengguna'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('pengguna.id_pengguna'))
    updated_at = db.Column(db.DateTime)
    validated_by = db.Column(db.Integer, db.ForeignKey('pengguna.id_pengguna'))
    validated_at = db.Column(db.DateTime)


class Kalimat(db.Model):
    __tablename__ = 'kalimat'
    id_kalimat = db.Column(db.Integer, primary_key=True, autoincrement=True)
    konten = db.Column(db.Text)
    status_validasi = db.Column(db.Boolean, default=False)
    id_kelompok = db.Column(db.Integer,)  # Menambahkan kolom id_kelompok yang tidak unique
    jenis_varian = db.Column(db.String,)  # Menambahkan kolom jenis_varian
    created_by = db.Column(db.Integer, db.ForeignKey('pengguna.id_pengguna'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('pengguna.id_pengguna'))
    updated_at = db.Column(db.DateTime)
    validated_by = db.Column(db.Integer, db.ForeignKey('pengguna.id_pengguna'))
    validated_at = db.Column(db.DateTime)


class LogAktivitas(db.Model):
    __tablename__ = 'log_aktivitas'
    id_log = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_pengguna = db.Column(db.Integer, db.ForeignKey('pengguna.id_pengguna'))
    waktu = db.Column(db.DateTime, default=datetime.utcnow)
    jenis_aktivitas = db.Column(db.String)
    detail_aktivitas = db.Column(db.Text)


class Varian(db.Model):
    __tablename__ = 'varian'
    id_varian = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_varian = db.Column(db.String, unique=True, nullable=False)
