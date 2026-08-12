# FitFlow — Project Context

## Project

FitFlow is a gym management platform.

Repository:
C:\Proyectos Web\FitFlow

Backend:
C:\Proyectos Web\FitFlow\backend

Application:
C:\Proyectos Web\FitFlow\backend\app

---

## Stack

Backend:
- Python
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- PostgreSQL
- Alembic
- Redis

Frontend:
- React
- TypeScript
- Vite
- Chakra UI
- TanStack Query
- Axios

---

## Backend Architecture

Router
  ↓
Service
  ↓
CRUD
  ↓
SQLAlchemy Model
  ↓
PostgreSQL

Pydantic schemas define API contracts.

Router:
HTTP, routing, dependencies, authentication,
authorization, response models.

Service:
business logic, domain rules, validation,
orchestration and calculations.

CRUD:
database access, queries, persistence,
filters, relationship loading and atomic operations.

SQLAlchemy:
ORM mapping, relationships and persistence.

---

## Domain

### Identity

User
- authentication/account
- roles

Person
- personal identity
- associated with User

Client
- gym client
- derived from Person

Teacher
- gym teacher
- derived from Person

Relationship:

User
  ↓ 1:1
Person
  ├── Client
  └── Teacher

---

### Membership

Client
  ↓
Membership
  ↓
Plan

Membership controls access to gym/classes.

Known plan concepts:

- gym_only
- classes
- premium
- personalized

Known membership states:

- active
- expired
- paused
- cancelled

---

### Classes

GymClass
  ↓
ClassSchedule
  ↓
ClassSession

ClassSchedule represents recurring scheduling.

RRULE is the recurrence source of truth.

ClassSession represents a concrete occurrence.

ClassSession contains concepts such as:

- starts_at
- ends_at
- capacity_snapshot
- status

---

### Booking

Client
  ↓
Booking
  ↓
ClassSession

Booking represents a client's reservation.

Booking states:

- confirmed
- cancelled
- attended
- no_show

Cancellation preserves booking history.

Booking creation may involve:

- membership validation
- allowed-plan validation
- capacity validation
- duplicate prevention
- transactional protection

---

### Attendance

Client
  ↓
Attendance

Attendance records client attendance/check-in.

---

## Main Domain Graph

User
└── Person
    ├── Client
    │   ├── Membership
    │   │   └── Plan
    │   ├── Booking
    │   └── Attendance
    │
    └── Teacher
        └── ClassSchedule
            └── ClassSession
                └── Booking

GymClass
└── ClassSchedule
    └── ClassSession

---

## ORM

Current ORM uses SQLAlchemy 2.x concepts:

- DeclarativeBase
- Mapped
- mapped_column
- relationship
- ForeignKey
- back_populates

Models include domain entities and shared mixins.

---

## Schemas

Pydantic v2 schemas are separated from ORM models.

Known schema patterns include:

- Base
- Create
- Update
- Public
- specialized response/view schemas

Examples include:

User
UserCreate
UserPublic
UserWithProfile
UserWithStats

Client
ClientPublic
ClientWithMembership
ClientWithBookings
ClientWithStats

Membership
MembershipCreate
MembershipPublic
MembershipWithClient
MembershipWithStats

ClassSchedule
ClassScheduleCreate
ClassSchedulePublic
ClassScheduleUpdate

ClassSession
ClassSessionCreate
ClassSessionPublic
ClassSessionWithRelations

Booking
BookingCreate
BookingPublic
BookingWithClient
BookingWithSession

---

## CRUD

CRUD classes exist for major domain entities.

Known examples:

- CRUDUser
- CRUDClient
- CRUDTeacher
- CRUDMembership
- CRUDGymClass
- CRUDClassSchedule
- CRUDClassSession
- CRUDBooking

Specialized CRUD operations exist for operations such as:

- client/user creation
- capacity checks
- session capacity snapshots
- booking lookup
- relationship loading
- filtered queries

---

## Authentication

Authentication/authorization uses:

- JWT
- roles
- Redis token/blacklist functionality

Known roles:

- admin
- teacher
- client
- front_desk

---

## Current Refactoring Context

Sprint 6.8 focused on:

- domain consolidation
- ORM/model refactoring
- Pydantic v2 migration
- removal of legacy `days_of_week`
- backend stabilization

Current work continues from this refactor.

`days_of_week` is legacy relative to the target architecture;
RRULE is the intended source of truth.

---

## Important Principle

This document is a compact map of the FitFlow domain and architecture.

It is NOT a substitute for the repository.

When implementation details matter:

inspect the actual source code.

Repository implementation is authoritative.