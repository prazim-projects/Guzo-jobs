# [YourAppName] – Ionic Vue PWA + Django & Graphene GraphQL

Modern full-stack application:  
**Frontend** — Ionic 7+ · Vue 3 · Progressive Web App  
**Backend**  — Django 4+/5+ · Graphene-Django (GraphQL)  
**Dependency management** — Pipenv (Python) · npm/pnpm/yarn (JS)

## 🚀 Quick Start

### Frontend – Ionic Vue PWA

```bash
# 1. Clone the repository
git clone https://github.com/prazim-projects/Guzo-jobs

#2 navigate to root of project
cd Guzo-jobs

# 3. Install dependencies
npm install
# or pnpm install
# or yarn install

# 4. Start development server
ionic serve
# ────────────────────────────────────────
# Alternative (Vite-only)
npm run dev
```

### Backend - Django Graphql API app contributors

```bash
# 1. Navigate to backend
cd guzo-jobs-back

# 2. (One-time) Install pipenv globally if you don't have it
# pip install pipenv

# 3. Install project dependencies & create virtual env
pipenv install

# 4. Sync exact locked versions (strongly recommended!)
# Do this after every git pull / branch switch
pipenv sync --dev

# 5. Activate the virtual environment
pipenv shell

# 6. Apply database migrations (first time only)
python manage.py migrate

# 7. Create a superuser (first time only)
python manage.py createsuperuser

# 8. Start the development server
python manage.py runserver
```