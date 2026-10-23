import type { Exam } from "./types";

const MOCK_EXAMS: Exam[] = [
  {
    id: 1,
    title: "Introduction to Algorithms",
    description:
      "Sorting, searching and Big-O analysis. Covers merge sort, quicksort, binary search and reasoning about the running time of simple loops.",
    duration_min: 90,
    status: "open",
  },
  {
    id: 2,
    title: "Database Design Fundamentals",
    description:
      "Entity-relationship modelling, normal forms up to BCNF, and writing joins and aggregate queries in SQL.",
    duration_min: 120,
    status: "published",
  },
  {
    id: 3,
    title: "Web Accessibility Quiz",
    description:
      "Short objective quiz on semantic HTML, colour contrast, keyboard navigation and labelling form controls.",
    duration_min: 45,
    status: "open",
  },
  {
    id: 4,
    title: "Operating Systems Midterm",
    description:
      "Processes and threads, CPU scheduling, deadlock conditions, paging and virtual memory. Includes two theory questions that ask you to explain your reasoning step by step with diagrams where they help.",
    duration_min: 150,
    status: "closed",
  },
  {
    id: 5,
    title: "Discrete Mathematics Practice",
    description: "",
    duration_min: 60,
    status: "draft",
  },
  {
    id: 6,
    title: "Computer Networks Final",
    description:
      "The TCP/IP model, routing, congestion control and DNS, with short-answer questions on packet traces.",
    duration_min: 180,
    status: "draft",
  },
];

const DEFAULT_DELAY_MS = 600;
const SLOW_DELAY_MS = 10_000;

function readMockScenario(): string | null {
  if (!import.meta.env.DEV) return null;
  return new URLSearchParams(window.location.search).get("mock");
}

export function loadExams(): Promise<Exam[]> {
  const scenario = readMockScenario();
  if (scenario === "error") {
    return Promise.reject(
      new Error("The exam list could not be loaded. Check your connection and try again."),
    );
  }
  const exams = scenario === "empty" ? [] : MOCK_EXAMS;
  const delayMs = scenario === "slow" ? SLOW_DELAY_MS : DEFAULT_DELAY_MS;

  return new Promise((resolve) => setTimeout(() => resolve(exams), delayMs));
}
