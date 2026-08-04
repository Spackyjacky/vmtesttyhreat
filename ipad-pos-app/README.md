# TillPoint — iPad EPOS App

A native SwiftUI/SwiftData iPad point-of-sale app: product & stock management,
a till/checkout screen, Bluetooth barcode scanner input, Bluetooth receipt
printing with cash-drawer trigger, barcode generation for un-barcoded stock,
and receipt emailing.

## Before you start: what you need

This is a real native iOS/iPadOS app, written in Swift. Building and
installing it on a physical iPad requires:

- **A Mac** with **Xcode** installed (free from the App Store).
- An **Apple ID** — a free one lets you build and run on your own iPad for
  testing (7-day resigning). A paid **Apple Developer Program** membership
  (£79/year) is needed for TestFlight or App Store distribution, or for
  builds that don't need re-signing every week.
- The **[XcodeGen](https://github.com/yonaskolb/XcodeGen)** tool to turn this
  folder into an `.xcodeproj` (`brew install xcodegen`). This keeps the
  project file out of git and avoids merge-conflict-prone `.xcodeproj` diffs.

This repository/session runs in a Linux container and cannot compile or run
iOS apps — there is no Xcode on Linux. Everything here is source code, ready
to open on a Mac.

## Getting it running

```bash
cd ipad-pos-app
brew install xcodegen   # one-time, if you don't have it
xcodegen generate
open TillPoint.xcodeproj
```

In Xcode:
1. Select the `TillPoint` project → `TillPoint` target → **Signing & Capabilities**.
2. Set your **Team** (your Apple ID) and adjust the **Bundle Identifier** if
   `com.yourcompany.tillpoint` is taken.
3. Plug in an iPad (or pick an iPad simulator for UI-only testing — Bluetooth
   won't work in the simulator), and hit **Run**.

No backend, server, or account is required — all data (products, stock,
sales, settings) is stored locally on the iPad using SwiftData.

## What's implemented

- **Till / checkout** — product grid with search, cart, cash/card/other
  payment, an on-screen cash keypad with quick "notes handed over" buttons
  (Exact, £5/£10/£20/£50) for fast cash tendered entry, automatic change
  calculation, receipt printing and cash drawer trigger on sale completion.
- **Products** — add/edit/delete, price, cost, tax rate, category, stock
  quantity, low-stock threshold, barcode field, and a **"Show on Till home
  screen"** toggle — turn it off for scan-only items you don't want
  cluttering the grid; they still ring up instantly by scan or search.
- **Barcode generation** — products with no barcode can get one generated
  on the spot (a GS1 in-store-use-range EAN-13-style number, rendered and
  printed as a CODE128 barcode) and printed as a label on your receipt
  printer.
- **Stock management** — stock list with low-stock filter, manual stock
  adjustments (restock, stock take, damaged, correction) with a full audit
  trail (`StockAdjustment` records). Stock is automatically decremented on
  sale and restored on void.
- **Sales history** — past receipts, reprint, email, void (restores stock).
- **Reports** — today's takings by payment method and top sellers.
- **Cashing up (Z-report)** — open the till with a starting float, watch
  live takings (transaction count, cash/card/other, expected cash in
  drawer) build up through the day, count the drawer at close using the
  same on-screen keypad, and get an instant over/short variance. Every
  closed session produces a full reconciliation report and stays in a
  "Past Sessions" history you can reopen any time.
- **Exportable stock report** — a CSV export from the Stock screen, with a
  choice of **All Stock** or **Low Stock Items Only**, handed to iOS's
  share sheet (save to Files, AirDrop, email, print, etc).
- **Dark mode** — System/Light/Dark appearance switch in Settings, on top
  of the app already using adaptive system colors throughout.
- **Bluetooth barcode scanner** — works out of the box with the vast
  majority of BLE (and USB) barcode scanners because they present themselves
  to iOS as a Bluetooth **keyboard** ("HID keyboard wedge"). Pair the
  scanner once in iPadOS **Settings → Bluetooth**, and the Till/product
  screens capture its scans automatically — no app-side pairing code needed.
  A camera-based fallback scanner (`CameraBarcodeScannerView`) is also
  included for when no hardware scanner is paired.
- **Bluetooth receipt printer + cash drawer** — `BluetoothPrinterManager`
  scans for and connects to any nearby BLE peripheral and looks for a
  writable characteristic to stream ESC/POS commands to. This covers the
  common cheap 58mm/80mm BLE thermal printers. The cash drawer is triggered
  by sending the standard ESC/POS "drawer kick" command (`ESC p`) to the
  printer, which fires the pulse out to the drawer connected to its RJ11
  port — this is how virtually all POS cash drawers are wired, so no
  separate drawer integration is needed.
- **Email receipts** — uses iOS's built-in Mail compose sheet
  (`MFMailComposeViewController`), so it sends from whatever Mail account is
  configured on the iPad, with no backend or API key required.

## Important hardware caveat

There are two very different kinds of "Bluetooth" printer:

- **BLE (Bluetooth Low Energy)** — what this app targets. No special Apple
  certification needed; `BluetoothPrinterManager` (built on `CoreBluetooth`)
  can talk to these directly.
- **Classic Bluetooth (SPP / serial)** — common on some older or higher-end
  commercial printers. Apple requires these to be **MFi-certified**, and
  your app would need Apple's **External Accessory** framework plus your own
  enrollment in the **MFi Program** to talk to them. That is *not* what's
  implemented here. If your printer/scanner hardware turns out to be
  Classic Bluetooth rather than BLE, check its spec sheet or manual before
  buying — most modern budget BLE POS printers (Munbyn, Rongta, Goojprt, and
  similar) will work with this app as-is.

Because `BluetoothPrinterManager` connects to *any* nearby writable BLE
peripheral rather than one hardcoded vendor's UUIDs, it should work broadly
— but exact receipt formatting (paper width, characters per line, specific
ESC/POS command support) can vary slightly by printer model. `EscPosBuilder`
assumes a 32-character-wide receipt (typical for 58mm paper); tweak
`ReceiptFormatter.padLine`'s `width` if you're using 80mm paper.

## Project structure

```
TillPoint/
  App/          App entry point, root navigation
  Models/       SwiftData models (Product, Sale, Stock, Settings, ...)
  Services/     Bluetooth printer manager, ESC/POS builder, barcode
                generator, scanner capture, mail composer, sale/stock logic
  Views/        SwiftUI screens, grouped by feature (Till, Products, Stock,
                Sales, Reports, Settings, Categories)
  Resources/    Asset catalog (app icon, accent color placeholders)
TillPointTests/ Unit tests for the ESC/POS builder and sale/stock logic
```

## Known limitations / good next steps

- Single-till, single-device only — no multi-till or cloud sync (by design,
  for this first version; see below if you want that later).
- No user accounts / staff PINs yet — `operatorName` fields exist in the
  data model ready for this.
- No partial refunds — void is all-or-nothing on a sale.
- No discounts/promotions on the till screen yet.
- Tax is modeled as a single VAT-inclusive rate per product; no multi-rate
  tax jurisdictions or exclusive-pricing mode.
- `BluetoothPrinterManager` connects to the first writable characteristic it
  finds — fine for single-purpose BLE printers, but if a printer exposes
  multiple writable services you may need to add filtering logic once you
  know its exact UUIDs.
- If you later want stock/sales to sync across multiple iPads (e.g. more
  than one till in the same shop), the models are already structured to
  make adding a Supabase/Firebase-style backend straightforward.

## Currency & locale

Defaults to GBP (`£`), changeable in **Settings → Tax & Currency**.
