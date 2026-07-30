# Atlas Invoice Studio

**Version:** 0.2.0-beta

---

# Mission

Build a professional desktop application that allows contractors to create
estimates and invoices in under two minutes.

The software must be:

- Fast
- Professional
- Reliable
- Easy to learn
- Easy to maintain

---

# Development Philosophy

Every feature must satisfy four requirements:

## 1. Solve a real business problem

If it doesn't help the contractor,
it does not belong in Version 1.

---

## 2. Keep it intuitive

The interface should require little or no explanation.

If we have to explain how to use it,
the design needs improvement.

---

## 3. Build software we would trust ourselves

Every feature should be stable enough that
we would confidently use it to run our own business.

---

## 4. Build for the future

Today's decisions should make tomorrow's features easier,
not harder.

---

# Current Five-Day Beta Target

Deliver a dependable single-user Windows desktop beta that Danny can use for
real painting and handyman work: manage customers and services, prepare
estimates, convert accepted estimates to invoices, generate professional PDFs,
configure his company identity, and protect local business data with backup and
restore.

## Client Profile

Danny is a solo handyman whose primary business is interior and exterior
painting. The beta prioritizes fast document creation, straightforward local
operation, professional customer-facing output, and recoverable data over
multi-user, cloud, or accounting-system features.

## Current Milestone: Company Settings and Data Protection

- Persistent company identity and document defaults
- Packaged-safe per-user application storage
- Managed company logo
- Local timestamped backup archives
- Validated restore with an automatic pre-restore safety backup

## Application Data and Migration

Source checkouts continue using the existing repository-local database at
`data/atlas_invoice_studio.db`, along with repository-local document and backup
folders. This preserves the current development workflow and data.

Packaged Windows builds use `%LOCALAPPDATA%/Atlas Invoice Studio/` for the live
database, generated documents, backups, and managed assets. On first packaged
startup only, Atlas copies an existing legacy project database when the new
per-user database does not exist. It never deletes the legacy database and
never overwrites an existing per-user database. Generated PDFs are excluded
from backup archives; they can be regenerated from saved documents.

---

# Project Roadmap

## Milestone 1 ✅

Project Foundation

- Dashboard
- Navigation
- Theme System
- SQLite
- Repository Pattern

Status:

COMPLETE

---

## Milestone 2

Customer Module

Status: COMPLETE

---

## Milestone 3

Estimate Module

Features

- New Estimate
- Line Items
- Totals
- Save
- Open
- Automatic Numbering

Status: COMPLETE

---

## Milestone 4

Invoice Module

Features

- Convert Estimate
- New Invoice
- Payment Tracking

Status: ESTIMATE-TO-INVOICE CONVERSION COMPLETE

Payment transaction tracking remains follow-up work.

---

## Milestone 5

PDF Engine

Features

- Professional Estimate PDF
- Professional Invoice PDF
- Print
- Preview

Status: ESTIMATE AND INVOICE PDF GENERATION COMPLETE

---

## Milestone 6

Company Settings and Data Protection

Features

- Company settings
- Safe packaged application paths
- Backup and restore

Status: IN PROGRESS

---

## Milestone 7

Client Release

Version 1.0

Installer

Documentation

Testing

Deployment

---

# Future Versions

Cloud Sync

Tablet Version

Phone Version

Customer Portal

Email Integration

Digital Signatures

Photos

Reports

Inventory

Scheduling

---

# Atlas Development Standards

Every milestone must be:

✓ Functional

✓ Tested

✓ Committed to Git

✓ Pushed to GitHub

before beginning the next milestone.

---

# Motto

"Professional software should be simple."
