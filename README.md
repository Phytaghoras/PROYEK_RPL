# Aksara Penerjemah

Aplikasi penerjemah aksara berbasis Flask.

## Persyaratan
- Python 3.8 atau lebih baru
- pip (package manager)

## Cara Menggunakan
1. **Clone repo ini**:
   ```bash
   git clone https://github.com/username/aksara-penerjemah.git
   cd aksara-penerjemah
   ```

2. **Buat virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Untuk macOS/Linux
   venv\Scripts\activate     # Untuk Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirement.txt
   ```

4. **Konfigurasikan file `.env`**:
   Buat file `.env` di folder root berdasarkan contoh di `env.example`.

5. **Jalankan aplikasi**:
   ```bash
   flask run
   ```

6. **Akses aplikasi**: Buka [http://localhost:5000](http://localhost:5000) di browser Anda.

## Migrasi Database
Jika menggunakan database, jalankan:
```bash
flask db init    # Hanya pertama kali
flask db migrate
flask db upgrade
