# Repair Shop — Setup Guide

This is a full-stack Next.js web app for managing your repair business.
It works on any device (phone, tablet, desktop) and can be installed as an app.

---

## What you need (all free tiers are sufficient to start)

| Service | Purpose | Free tier |
|---|---|---|
| [Supabase](https://supabase.com) | Database, auth, file storage | Yes — 500 MB DB, 1 GB storage |
| [Twilio](https://twilio.com) | SMS notifications | Trial credit included |
| [Resend](https://resend.com) | Email notifications | 3,000 emails/month free |
| [Vercel](https://vercel.com) | Hosting | Yes — free for hobby |

---

## Step 1 — Supabase setup

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Click **New project** → choose a name (e.g. "repair-shop") and set a database password
3. Wait ~2 minutes for the project to spin up
4. Go to **SQL Editor** (left sidebar) → paste the entire contents of `supabase/schema.sql` → click **Run**
5. Go to **Storage** → click **New bucket** → name it `repair-media` → tick **Public bucket** → Save
6. Go to **Settings → API** and copy:
   - `Project URL` → `NEXT_PUBLIC_SUPABASE_URL`
   - `anon public` key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (**keep this secret**)

### Create your first staff account
In Supabase → **Authentication → Users** → **Invite user** → enter your email.
You'll receive an email to set your password.

---

## Step 2 — Twilio setup (SMS)

1. Go to [twilio.com](https://twilio.com) → create a free account
2. Verify your phone number during signup
3. On the Console Dashboard, copy:
   - **Account SID** → `TWILIO_ACCOUNT_SID`
   - **Auth Token** → `TWILIO_AUTH_TOKEN`
4. Go to **Phone Numbers → Manage → Buy a number** (or use the trial number)
   - Copy the number → `TWILIO_PHONE_NUMBER` (format: `+441234567890`)

> **Trial accounts**: SMS can only be sent to verified numbers. Upgrade when you go live.

---

## Step 3 — Resend setup (Email)

1. Go to [resend.com](https://resend.com) → create a free account
2. Go to **API Keys** → **Create API Key** → copy it → `RESEND_API_KEY`
3. Go to **Domains** → add and verify your domain (e.g. `yourshop.com`)
4. Set `RESEND_FROM_EMAIL` to something like `repairs@yourshop.com`

> Without a verified domain, Resend will only send to your own email address.
> You can skip this initially and add it when you're ready to go live.

---

## Step 4 — Environment variables

```bash
cp .env.example .env.local
```

Open `.env.local` and fill in every value using the credentials from steps 1-3.

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_PHONE_NUMBER=+441234567890

RESEND_API_KEY=re_xxxx
RESEND_FROM_EMAIL=repairs@yourshop.com
RESEND_FROM_NAME=My Repair Shop

NEXT_PUBLIC_APP_NAME=My Repair Shop
NEXT_PUBLIC_APP_URL=https://your-vercel-url.vercel.app
NEXT_PUBLIC_SHOP_PHONE=01234 567890
```

---

## Step 5 — Run locally

```bash
cd repair-shop
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — you'll be redirected to the login page.

---

## Step 6 — Deploy to Vercel (free hosting)

1. Push this project to GitHub (you can create a private repo)
2. Go to [vercel.com](https://vercel.com) → **New Project** → import your GitHub repo
3. Set the **Root Directory** to `repair-shop`
4. In **Environment Variables**, add all the same values from `.env.local`
5. Click **Deploy**

After deployment, update `NEXT_PUBLIC_APP_URL` in Vercel to your production URL.

---

## Step 7 — Install as an app (optional but recommended)

**On iPhone/iPad:**
- Open Safari → navigate to your Vercel URL
- Tap Share → **Add to Home Screen**

**On Android:**
- Open Chrome → navigate to your Vercel URL
- Tap the three dots → **Install app** (or **Add to Home Screen**)

**On desktop (Chrome/Edge):**
- Click the install icon in the address bar

---

## How to use

### Creating a ticket (under 60 seconds)
1. Tap **New Repair Ticket** in the sidebar or on the dashboard
2. **Step 1:** Search for an existing customer or add a new one (or skip for walk-ins)
3. **Step 2:** Select device type, enter make/model, IMEI (if phone), and fault description
4. **Step 3:** Take intake photos, note any pre-existing damage, then click **Create Ticket**

### Updating job status + notifying customers
- Open a job → use the status pipeline at the top
- Clicking the next status automatically sends an SMS + email to the customer
- Status messages are pre-written but you can customise them in `types/index.ts`

### Digital signature at collection
1. When a job is marked **Ready**, copy the collection link from the job page
2. Send the link to the customer (WhatsApp, SMS, etc.) or open it on your counter device
3. The customer reviews their repair details, photographs of intake damage, and signs
4. The device is marked **Collected** with a timestamped signature record

### Inventory & parts
- Go to **Inventory** to add your parts stock
- Set a **reorder threshold** — the dashboard will warn you when stock falls below it
- When working on a job, add parts from the job detail page — stock automatically decrements

---

## Customisation

| What | Where |
|---|---|
| Shop name / phone | `.env.local` → `NEXT_PUBLIC_APP_NAME`, `NEXT_PUBLIC_SHOP_PHONE` |
| SMS messages per status | `types/index.ts` → `STATUS_NOTIFICATION_MESSAGES` |
| Colour scheme | `tailwind.config.ts` → `colors` |
| Add staff accounts | Supabase → Authentication → Users → Invite user |

---

## File structure

```
repair-shop/
├── app/
│   ├── (auth)/login/          # Login page
│   ├── (dashboard)/           # Protected pages (Dashboard, Jobs, Customers, Inventory)
│   ├── collect/[id]/          # Public collection + signature page
│   └── api/                   # REST API routes
├── components/                # Reusable UI components
├── lib/                       # Supabase, Twilio, Resend helpers
├── types/                     # TypeScript types + constants
├── supabase/schema.sql        # Database schema — run once in Supabase SQL Editor
└── SETUP.md                   # This file
```
