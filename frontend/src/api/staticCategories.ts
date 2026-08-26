import type { CategoryOut } from "./types";

// Mirrors api/categories.py's CATEGORY_ID_MAP - kept in sync manually. Needed on the
// Request screen so category chips render before any classify call has happened.
export const STATIC_CATEGORIES: CategoryOut[] = [
  { id: "project-management", name: "Project Management Software" },
  { id: "hiring-hr", name: "Hiring and HR Software" },
  { id: "event-registration-ticketing", name: "Event Registration and Ticketing Software" },
  { id: "crm", name: "End-to-End CRM Software" },
  { id: "tax-filing", name: "Tax Filing Software" },
  { id: "email-marketing", name: "Email Marketing Software" },
];
