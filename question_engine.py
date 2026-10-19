"""
AI Interview - Question Engine
Ensures questions are:
1. Never repeated across interviews for a candidate/session.
2. Formed on the basis of candidate's Resume (specific skills, tools, projects).
3. Formed on the basis of the User's Target Job Role (Python Developer, Web Developer, Data Analyst, etc.).
"""

import os
import re
import json
import random
import sqlite3

def normalize_question(q):
    """Normalize question text to check for duplicates."""
    return re.sub(r"[^a-z0-9]", "", (q or "").lower())

def get_previously_asked_questions(db_path, candidate_name=None, limit=50):
    """
    Retrieve normalized question texts asked in previous sessions to prevent repetition.
    """
    used = set()
    if not os.path.exists(db_path):
        return used
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = []
            if candidate_name and candidate_name.strip() and candidate_name.strip().lower() != "candidate":
                c_rows = conn.execute(
                    "SELECT details_json FROM interviews WHERE LOWER(candidate) = LOWER(?) ORDER BY id DESC LIMIT ?",
                    (candidate_name.strip(), limit)
                ).fetchall()
                rows.extend(c_rows)
            # Also include recent sessions to avoid repetition in general
            recent_rows = conn.execute(
                "SELECT details_json FROM interviews ORDER BY id DESC LIMIT 15"
            ).fetchall()
            rows.extend(recent_rows)

            for row in rows:
                try:
                    details = json.loads(row["details_json"])
                    for item in details:
                        q_text = item.get("question", "")
                        if q_text:
                            norm = normalize_question(q_text)
                            if norm:
                                used.add(norm)
                except Exception:
                    pass
    except Exception as exc:
        print("Question engine DB check error:", exc)
    return used

# Comprehensive technical skills dictionary with synonyms
SKILL_CATALOG = {
    "Python": ["python", "python3", "django", "flask", "fastapi", "pytest", "numpy", "pandas"],
    "JavaScript": ["javascript", "js", "ecmascript", "es6", "node", "nodejs", "express"],
    "TypeScript": ["typescript", "ts", "angular", "nest", "nestjs"],
    "React": ["react", "reactjs", "react.js", "nextjs", "next.js", "redux"],
    "SQL": ["sql", "mysql", "postgresql", "postgres", "sqlite", "oracle", "plsql"],
    "HTML/CSS": ["html", "html5", "css", "css3", "sass", "scss", "tailwind", "bootstrap"],
    "Java": ["java", "spring", "springboot", "spring boot", "hibernate", "maven"],
    "C++": ["c++", "cpp", "stl", "pointers"],
    "C": ["c programming", "c language"],
    "Data Structures": ["data structures", "dsa", "algorithms", "binary tree", "linked list", "graph", "hash map"],
    "Git": ["git", "github", "gitlab", "version control"],
    "Docker": ["docker", "container", "containers", "dockerfile", "docker-compose"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda", "cloud"],
    "Machine Learning": ["machine learning", "ml", "deep learning", "ai", "scikit-learn", "tensorflow", "pytorch"],
    "Pandas": ["pandas", "data analysis", "data analytics", "dataframe"],
    "MongoDB": ["mongodb", "nosql", "mongoose"],
    "REST APIs": ["rest api", "restful", "api integration", "postman", "endpoint"],
    "Linux": ["linux", "bash", "shell scripting", "ubuntu"],
    "Excel": ["excel", "spreadsheets", "vlookup"],
    "Communication": ["communication", "teamwork", "leadership", "agile", "scrum"]
}

def extract_resume_details(resume_text):
    """
    Extract skills and project highlights from resume text.
    """
    if not resume_text or not resume_text.strip():
        return {"skills": [], "projects": []}

    text_lower = resume_text.lower()
    matched_skills = []

    for skill_name, triggers in SKILL_CATALOG.items():
        for trigger in triggers:
            pattern = r"\b" + re.escape(trigger) + r"\b"
            if re.search(pattern, text_lower):
                matched_skills.append(skill_name)
                break

    # Extract detected project titles or highlights
    projects = []
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    in_projects_sec = False
    for line in lines:
        l_lower = line.lower()
        if any(h in l_lower for h in ["projects", "personal projects", "academic projects", "key projects"]):
            in_projects_sec = True
            continue
        if in_projects_sec and any(h in l_lower for h in ["experience", "education", "skills", "certifications", "hobbies"]):
            in_projects_sec = False
            break
        if in_projects_sec:
            if re.match(r"^[-•*#\d\.]+\s*", line) or (len(line) < 60 and line.isupper()):
                clean_p = re.sub(r"^[-•*#\d\.]+\s*", "", line).strip()
                if 4 < len(clean_p) < 80:
                    projects.append(clean_p)

    return {
        "skills": matched_skills[:10],
        "projects": projects[:4]
    }

# ============================================================================
# RESUME-BASED QUESTION POOL (Directly based on candidate's resume skills)
# ============================================================================

RESUME_MCQ_BANK = {
    "Python": [
        {
            "question": "Your resume highlights Python: What is the main difference between a list and a tuple in Python?",
            "options": ["Lists are immutable while tuples are mutable", "Lists are mutable while tuples are immutable", "Tuples cannot store integers", "Lists cannot be nested"],
            "correct_index": 1,
            "topic": "Python Data Types",
            "explanation": "Lists can be modified after creation (mutable), whereas tuples cannot be changed (immutable)."
        },
        {
            "question": "Regarding Python on your resume: What does the `yield` keyword do inside a function?",
            "options": ["Terminates the program immediately", "Converts the function into a generator", "Throws a custom exception", "Declares a global variable"],
            "correct_index": 1,
            "topic": "Python Generators",
            "explanation": "`yield` pauses the function and returns an iterator object, turning the function into a generator."
        },
        {
            "question": "Based on your Python skill: Which dictionary method safely retrieves a value without raising a KeyError if the key is missing?",
            "options": ["dict.fetch(key)", "dict.get(key, default)", "dict.find(key)", "dict.lookup(key)"],
            "correct_index": 1,
            "topic": "Python Dictionaries",
            "explanation": "`dict.get(key, default)` returns the default value (or None) if the key is not in the dictionary."
        },
        {
            "question": "From your Python background: What is the purpose of Python's `with` statement (context manager)?",
            "options": ["To run loops asynchronously", "To automatically allocate and release resources such as file handles", "To define multithreading locks only", "To speed up math computations"],
            "correct_index": 1,
            "topic": "Python Context Managers",
            "explanation": "Context managers ensure resources like files and network connections are cleanly closed even if exceptions occur."
        }
    ],
    "React": [
        {
            "question": "Your resume includes React: What is the effect of passing an empty dependency array `[]` to `useEffect`?",
            "options": ["It runs on every re-render", "It runs once when the component mounts", "It disables the effect entirely", "It triggers an infinite render loop"],
            "correct_index": 1,
            "topic": "React Hooks",
            "explanation": "An empty dependency array ensures the effect runs only once after the initial render."
        },
        {
            "question": "Based on React on your resume: Why must you avoid directly mutating state (e.g. `state.count = 5`)?",
            "options": ["Direct mutation is a syntax error in JSX", "React cannot detect the change and will not re-render the component", "It immediately deletes all child components", "It forces synchronous page reloads"],
            "correct_index": 1,
            "topic": "React State Management",
            "explanation": "React relies on immutability and state setters to track changes and schedule component re-renders."
        },
        {
            "question": "From your React experience: What is the primary purpose of the `useMemo` hook?",
            "options": ["To memoize expensive calculation results between renders", "To fetch data from backend REST APIs", "To update browser cookies", "To animate DOM elements"],
            "correct_index": 0,
            "topic": "React Performance",
            "explanation": "`useMemo` caches the result of a calculation between re-renders when dependencies haven't changed."
        }
    ],
    "SQL": [
        {
            "question": "Your resume mentions SQL: Which clause is used to filter aggregated data produced by a `GROUP BY` statement?",
            "options": ["WHERE", "HAVING", "FILTER", "ORDER BY"],
            "correct_index": 1,
            "topic": "SQL Filtering",
            "explanation": "`WHERE` filters individual rows before aggregation; `HAVING` filters groups after aggregation."
        },
        {
            "question": "Based on SQL from your resume: What is the difference between `UNION` and `UNION ALL`?",
            "options": ["UNION removes duplicate rows while UNION ALL keeps all duplicates", "UNION ALL is slower because it sorts records", "UNION only works on single tables", "There is no difference"],
            "correct_index": 0,
            "topic": "SQL Joins & Sets",
            "explanation": "`UNION` performs a distinct operation to remove duplicates, whereas `UNION ALL` retains all rows and is faster."
        },
        {
            "question": "Regarding SQL on your resume: What is the primary benefit of creating an index on a database table column?",
            "options": ["It automatically encrypts the column data", "It accelerates SELECT queries by enabling faster lookups", "It eliminates the need for foreign keys", "It allows multiple primary keys in one table"],
            "correct_index": 1,
            "topic": "Database Indexing",
            "explanation": "Indexes provide quick lookup data structures (like B-Trees) that dramatically speed up search and join operations."
        }
    ],
    "JavaScript": [
        {
            "question": "Your resume lists JavaScript: What is the difference between `==` and `===` in JavaScript?",
            "options": ["`==` compares value and type; `===` only compares value", "`===` compares both value and type without type coercion", "`==` is deprecated in modern ES6", "There is no functional difference"],
            "correct_index": 1,
            "topic": "JavaScript Operators",
            "explanation": "Strict equality `===` checks both value and type without performing implicit type coercion."
        },
        {
            "question": "Based on JavaScript on your resume: What does `typeof null` evaluate to in JavaScript?",
            "options": ["'null'", "'undefined'", "'object'", "'boolean'"],
            "correct_index": 2,
            "topic": "JavaScript Types",
            "explanation": "In JavaScript, `typeof null` historically evaluates to `'object'`, which is a known language quirk."
        },
        {
            "question": "From your JavaScript background: Which array method creates a new array populated with the results of calling a function on every element?",
            "options": ["filter()", "map()", "reduce()", "forEach()"],
            "correct_index": 1,
            "topic": "JavaScript Arrays",
            "explanation": "`map()` transforms each element and returns a new array of the same length."
        }
    ],
    "Git": [
        {
            "question": "Your resume features Git: Which command creates and switches to a new Git branch in a single step?",
            "options": ["git branch -new <name>", "git checkout -b <name>", "git switch --all <name>", "git merge -b <name>"],
            "correct_index": 1,
            "topic": "Git Branching",
            "explanation": "`git checkout -b <name>` (or `git switch -c <name>`) creates the branch and checks it out immediately."
        },
        {
            "question": "Based on Git on your resume: What is the key difference between `git pull` and `git fetch`?",
            "options": ["`git fetch` downloads remote changes and merges them automatically", "`git fetch` only downloads changes to your local repo without merging them", "`git pull` never modifies local files", "`git fetch` deletes remote branches"],
            "correct_index": 1,
            "topic": "Git Workflows",
            "explanation": "`git fetch` updates your remote-tracking branches; `git pull` does a fetch followed by merging into your active branch."
        }
    ],
    "Docker": [
        {
            "question": "Your resume includes Docker: What is the relationship between a Docker image and a Docker container?",
            "options": ["A container is an inactive image", "A container is a runnable, isolated instance of an image", "An image is created only after running a container", "They are identical terms"],
            "correct_index": 1,
            "topic": "Docker Basics",
            "explanation": "An image is a read-only blueprint; a container is a live running execution environment created from that blueprint."
        },
        {
            "question": "From your Docker skill: What is the main benefit of multi-stage Docker builds?",
            "options": ["To run multiple operating systems at once", "To reduce final production image size by separating build tools from runtime assets", "To bypass container security policies", "To compile code faster on the host machine"],
            "correct_index": 1,
            "topic": "Docker Optimization",
            "explanation": "Multi-stage builds allow you to keep build-time compilers and dependencies out of the final slim runtime image."
        }
    ],
    "Machine Learning": [
        {
            "question": "Your resume features Machine Learning: What does 'overfitting' mean in a model?",
            "options": ["The model performs poorly on training data but well on test data", "The model learns training noise and details too well, failing to generalize to unseen test data", "The model runs out of memory during inference", "The learning rate is set too low"],
            "correct_index": 1,
            "topic": "ML Generalization",
            "explanation": "Overfitting happens when a model fits the training set too closely and fails to make accurate predictions on new data."
        },
        {
            "question": "Based on ML on your resume: Why is data commonly split into training and test sets?",
            "options": ["To make the training run twice as fast", "To evaluate how well the model generalizes to unseen data", "Because algorithms cannot process complete datasets", "To remove all duplicate entries automatically"],
            "correct_index": 1,
            "topic": "ML Evaluation",
            "explanation": "Testing on held-out data gives an unbiased estimate of the model's true performance in production."
        }
    ],
    "Data Structures": [
        {
            "question": "Your resume notes Data Structures: What is the average time complexity of searching for an element in a Hash Table?",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n^2)"],
            "correct_index": 0,
            "topic": "Hash Table Complexity",
            "explanation": "Hash tables compute an index via a hash function, yielding O(1) average time complexity for lookups."
        },
        {
            "question": "Regarding Data Structures on your resume: Which data structure is best suited for implementing a FIFO (First-In, First-Out) buffer?",
            "options": ["Stack", "Queue", "Max Heap", "Binary Search Tree"],
            "correct_index": 1,
            "topic": "Queue Operations",
            "explanation": "A Queue operates on the First-In, First-Out principle, making it ideal for buffers and task scheduling."
        }
    ],
    "Java": [
        {
            "question": "Your resume highlights Java: What is the difference between method overloading and method overriding?",
            "options": ["Overloading occurs in subclasses; overriding occurs in the same class", "Overloading has the same name with different parameters in the same class; overriding redefines a parent method in a subclass", "They are identical in Java 8 and above", "Overriding does not support the `@Override` annotation"],
            "correct_index": 1,
            "topic": "Java OOP",
            "explanation": "Overloading allows multiple methods with identical names but different signatures; overriding re-implements a superclass method."
        }
    ],
    "HTML/CSS": [
        {
            "question": "Your resume mentions HTML/CSS: In the CSS Box Model, which layer is positioned between padding and margin?",
            "options": ["Content", "Border", "Outline", "Clip path"],
            "correct_index": 1,
            "topic": "CSS Box Model",
            "explanation": "From inside out: Content -> Padding -> Border -> Margin."
        }
    ]
}

RESUME_TEXT_BANK = {
    "default": [
        "In your resume, you highlighted {skill}. Can you explain a practical problem or feature you implemented using it, and how you approached the solution?",
        "Your resume notes experience with {skill}. What were the key technical decisions and trade-offs you made when using this technology in your projects?",
        "Referencing your work with {skill} on your resume: Describe a tricky bug or performance issue you encountered, and how you diagnosed and resolved it.",
        "Your resume mentions {project_ref}. What was your specific architectural contribution to this, and what would you improve if rebuilding it today?",
        "Based on your resume experience in {skill}: How did you handle testing, error validation, and code maintainability in that implementation?"
    ]
}

# ============================================================================
# ROLE-BASED QUESTION POOL (Directly based on candidate's target job role)
# ============================================================================

ROLE_MCQ_BANK = {
    "Python Developer": [
        {
            "question": "As a Python Developer: How does CPython's Global Interpreter Lock (GIL) impact multithreaded applications?",
            "options": ["It prevents multiple threads from executing Python bytecode simultaneously on multiple CPU cores", "It makes all database queries execute asynchronously", "It compiles Python script into C++ code", "It removes the need for memory garbage collection"],
            "correct_index": 0,
            "topic": "Python GIL & Concurrency",
            "explanation": "The GIL ensures only one thread executes Python bytecode at a time, making multiprocessing preferable for CPU-bound tasks."
        },
        {
            "question": "For a Python Developer role: What is the primary difference between `is` and `==` in Python?",
            "options": ["`is` compares object identity (memory location), while `==` compares object values/equality", "`is` is used for strings; `==` is used for integers", "`==` compares memory addresses", "They are completely interchangeable"],
            "correct_index": 0,
            "topic": "Python Internals",
            "explanation": "`is` checks whether two variables point to the exact same object in memory; `==` checks value equality."
        },
        {
            "question": "Python Developer question: What will happen when a function defines `def func(a, b=[]): b.append(a); return b` and is called multiple times?",
            "options": ["A new empty list is created on each call", "The default list is created once at definition time and retains values across calls", "A TypeError is raised on the second call", "Python automatically clears default arguments after return"],
            "correct_index": 1,
            "topic": "Python Mutable Defaults",
            "explanation": "Default argument expressions are evaluated once when the function is defined, so mutable defaults persist mutations across calls."
        },
        {
            "question": "Python Developer question: What is the time complexity of looking up a key in a standard Python dictionary with good hashing?",
            "options": ["O(1) average time", "O(log n) time", "O(n) time", "O(n log n) time"],
            "correct_index": 0,
            "topic": "Python Performance",
            "explanation": "Python dictionaries are implemented as optimized hash tables, achieving O(1) average lookup time."
        },
        {
            "question": "In Python Development: Which built-in module is standard for writing automated unit tests and test suites?",
            "options": ["tester", "unittest", "pycheck", "assertlib"],
            "correct_index": 1,
            "topic": "Python Testing",
            "explanation": "`unittest` is Python's built-in unit testing framework, inspired by JUnit."
        }
    ],
    "Web Developer": [
        {
            "question": "As a Web Developer: What is the primary difference between CSS Grid and CSS Flexbox?",
            "options": ["Grid is two-dimensional (rows and columns); Flexbox is primarily one-dimensional (row or column)", "Flexbox is only for mobile screens; Grid is only for desktops", "Grid cannot align items vertically", "Flexbox requires external JavaScript libraries"],
            "correct_index": 0,
            "topic": "Web Layouts",
            "explanation": "CSS Grid is designed for 2D layouts (rows + columns), whereas Flexbox is designed for 1D layouts (single row or column)."
        },
        {
            "question": "For a Web Developer role: What does the HTTP 403 Forbidden status code indicate?",
            "options": ["The requested resource was not found on the server", "The server understood the request but refuses to authorize it", "The user supplied bad syntax in the request body", "The server timed out waiting for the gateway"],
            "correct_index": 1,
            "topic": "HTTP Protocols",
            "explanation": "403 Forbidden means the server recognizes the caller's identity or credentials, but access rights prevent access."
        },
        {
            "question": "Web Developer question: In the browser event flow, what is 'Event Bubbling'?",
            "options": ["Events start at the target element and propagate upwards through parent elements in the DOM tree", "Events move from window down to target element", "Events are discarded when users scroll", "Events only fire on form inputs"],
            "correct_index": 0,
            "topic": "DOM Event Model",
            "explanation": "Event bubbling is the phase where an event triggers on the inner target element and bubbles up through ancestor nodes."
        },
        {
            "question": "Web Developer question: What is Cross-Origin Resource Sharing (CORS)?",
            "options": ["A mechanism allowing a server to specify which foreign origins can access its resources via browser headers", "A CSS preprocessor for styling components", "A database indexing protocol", "A tool for compressing web images"],
            "correct_index": 0,
            "topic": "Web Security",
            "explanation": "CORS is a security standard enforced by browsers that uses HTTP headers to govern cross-origin HTTP requests."
        },
        {
            "question": "Web Developer question: Which HTTP method should be idempotent and used to retrieve representation of a resource without side effects?",
            "options": ["POST", "GET", "PATCH", "CONNECT"],
            "correct_index": 1,
            "topic": "RESTful Principles",
            "explanation": "GET requests must be safe and idempotent, meaning repeated requests produce the same state without modifying server data."
        }
    ],
    "Software Developer": [
        {
            "question": "For a Software Developer role: In the SOLID design principles, what does the 'Single Responsibility Principle' state?",
            "options": ["A class should have only one reason to change, meaning only one primary job", "Every program should have only a single main function", "A function must never accept more than one argument", "Developers should work on one task per week"],
            "correct_index": 0,
            "topic": "SOLID Principles",
            "explanation": "The Single Responsibility Principle (SRP) dictates that a module or class should be responsible to only one actor or reason to change."
        },
        {
            "question": "Software Developer question: What is the main benefit of Continuous Integration (CI)?",
            "options": ["Eliminates the need for writing unit tests", "Automatically builds and runs tests on code commits to detect integration issues early", "Replaces version control branches", "Writes documentation automatically without human input"],
            "correct_index": 1,
            "topic": "Software Lifecycle",
            "explanation": "CI automates code compilation and automated test execution with each commit, finding merge and logic bugs quickly."
        },
        {
            "question": "Software Developer question: Which design pattern provides a single point of access to an instance throughout an application?",
            "options": ["Singleton Pattern", "Factory Method", "Observer Pattern", "Strategy Pattern"],
            "correct_index": 0,
            "topic": "Design Patterns",
            "explanation": "The Singleton pattern restricts class instantiation to a single instance and provides global access to it."
        },
        {
            "question": "Software Developer question: What is the purpose of mock objects in automated unit testing?",
            "options": ["To simulate complex dependencies (like databases or third-party APIs) so unit tests run in isolation and fast", "To generate fake user passwords", "To replace compilers in continuous deployment", "To measure network bandwidth"],
            "correct_index": 0,
            "topic": "Unit Testing",
            "explanation": "Mocks simulate behavior of external dependencies, enabling deterministic, isolated, and fast unit test runs."
        },
        {
            "question": "Software Developer question: What does ACID stand for in relational database transactions?",
            "options": ["Atomicity, Consistency, Isolation, Durability", "Accuracy, Control, Integration, Distribution", "Array, Class, Inheritance, Delegation", "Asynchronous, Concurrent, Indexed, Distributed"],
            "correct_index": 0,
            "topic": "Database Architecture",
            "explanation": "ACID properties ensure reliable database transaction processing even during power failures or crashes."
        }
    ],
    "Data Analyst": [
        {
            "question": "As a Data Analyst: What is the difference between an INNER JOIN and a LEFT JOIN in SQL?",
            "options": ["INNER JOIN returns only rows with matches in both tables; LEFT JOIN returns all rows from the left table and matching rows from the right", "LEFT JOIN only returns columns starting with the letter L", "INNER JOIN deletes unmatched records from the database", "They produce identical row sets in all databases"],
            "correct_index": 0,
            "topic": "SQL Data Analysis",
            "explanation": "An INNER JOIN selects records with matching values in both tables; a LEFT JOIN keeps every row from the left table regardless."
        },
        {
            "question": "For a Data Analyst role: When analyzing a skewed income dataset with extreme high outliers, which measure of central tendency is most reliable?",
            "options": ["Mean", "Median", "Mode", "Variance"],
            "correct_index": 1,
            "topic": "Statistics for Analytics",
            "explanation": "The median represents the 50th percentile and is robust against extreme outliers, whereas the mean is heavily skewed."
        },
        {
            "question": "Data Analyst question: In Python's Pandas library, what is the difference between `.loc` and `.iloc`?",
            "options": [".loc is label-based indexing; .iloc is integer position-based indexing", ".loc is for column deletion; .iloc is for row addition", ".loc is slower than a Python loop", "There is no difference"],
            "correct_index": 0,
            "topic": "Pandas DataFrames",
            "explanation": "`.loc` selects by index/column labels; `.iloc` selects strictly by zero-based integer positional coordinates."
        },
        {
            "question": "Data Analyst question: What does a Pearson correlation coefficient of -0.85 between two variables signify?",
            "options": ["No relationship whatsoever", "A strong negative linear correlation", "A calculation error", "A strong positive exponential relationship"],
            "correct_index": 1,
            "topic": "Statistical Analysis",
            "explanation": "A correlation near -1 indicates a strong negative linear association: as one variable increases, the other decreases."
        },
        {
            "question": "Data Analyst question: What is the primary purpose of a Box Plot (Box-and-Whisker diagram)?",
            "options": ["To display continuous time series trends", "To visualize data distribution, median, quartiles, and detect potential outliers", "To replace SQL database schemas", "To compare text sentiment scores"],
            "correct_index": 1,
            "topic": "Data Visualization",
            "explanation": "Box plots summarize distributions through quartiles and highlight outliers outside 1.5 * IQR."
        }
    ],
    "Computer Science Student": [
        {
            "question": "For a Computer Science Student: What is the fundamental difference between a Process and a Thread?",
            "options": ["A process has its own dedicated address space; threads within the same process share that memory space", "A thread cannot execute code", "A process is managed only by hardware chips", "Threads cannot communicate with each other"],
            "correct_index": 0,
            "topic": "Operating Systems",
            "explanation": "Processes are independent execution units with private memory; threads are lightweight execution paths sharing the process's memory."
        },
        {
            "question": "CS Student question: What is the worst-case time complexity of standard QuickSort without randomized pivot selection?",
            "options": ["O(log n)", "O(n)", "O(n log n)", "O(n^2)"],
            "correct_index": 3,
            "topic": "Algorithms & Complexity",
            "explanation": "When the pivot chosen is consistently the smallest or largest element (e.g. sorted input with end pivot), QuickSort degrades to O(n^2)."
        },
        {
            "question": "CS Student question: Which layer of the OSI model is responsible for end-to-end data transmission and port-to-port connections (e.g. TCP, UDP)?",
            "options": ["Data Link Layer", "Network Layer", "Transport Layer", "Session Layer"],
            "correct_index": 2,
            "topic": "Computer Networks",
            "explanation": "The Transport Layer (Layer 4) handles host-to-host communication, segmentation, flow control, and reliability (TCP/UDP)."
        },
        {
            "question": "CS Student question: In memory management, what causes a Page Fault?",
            "options": ["A hardware CPU failure", "An attempt to access a virtual memory page that is not currently mapped into physical RAM", "A syntax error in a C program", "Disconnecting the network cable"],
            "correct_index": 1,
            "topic": "Virtual Memory",
            "explanation": "A page fault is an interrupt raised by the hardware MMU when a program accesses a page not loaded in physical memory."
        },
        {
            "question": "CS Student question: Which data structure is used by the operating system call stack to manage function call activation records?",
            "options": ["Queue", "Stack", "Binary Search Tree", "Linked List"],
            "correct_index": 1,
            "topic": "Data Structures & Systems",
            "explanation": "The call stack follows LIFO (Last In, First Out) order to handle function calls and local variable frame returns."
        }
    ],
    "General": [
        {
            "question": "For a general engineering role: What is the first step you should take when diagnosing an unexpected bug in an application?",
            "options": ["Immediately rewrite the whole codebase", "Reproduce the issue consistently and inspect error logs or stack traces", "Blame the operating system", "Deploy to production to see if it fixes itself"],
            "correct_index": 1,
            "topic": "Debugging Methodology",
            "explanation": "Effective debugging begins by reliably reproducing the bug and analyzing error logs and stack traces."
        },
        {
            "question": "General technical question: What is the main advantage of using version control (like Git) in collaborative software projects?",
            "options": ["It tracks all changes, allows parallel development through branches, and enables reverting breaking edits", "It eliminates the need for software testing", "It prevents all syntax errors automatically", "It compiles code into machine instructions"],
            "correct_index": 0,
            "topic": "Software Collaboration",
            "explanation": "Version control provides history, branch management, collaboration merging, and auditability."
        }
    ]
}

ROLE_TEXT_BANK = {
    "Python Developer": [
        "As a candidate for Python Developer: Explain how Python manages memory, how reference counting works, and how Python resolves circular references.",
        "As a Python Developer: How would you use decorators to implement logging or caching in a web backend service? Give a concrete example.",
        "Python Developer question: Compare multithreading versus multiprocessing in Python. When would you choose one over the other for a production application?",
        "For a Python Developer role: Walk me through how you structure, configure, and isolate dependencies in a production-ready Python project."
    ],
    "Web Developer": [
        "As a candidate for Web Developer: Explain how the browser's JavaScript Event Loop handles the microtask queue versus the macrotask queue.",
        "For a Web Developer role: What practical steps do you take to improve web application performance, core web vitals, and initial page load speed?",
        "Web Developer question: Walk me through how you design and implement responsive layouts that function seamlessly across mobile, tablet, and desktop screens.",
        "As a Web Developer: How do you protect frontend web applications against common security threats like Cross-Site Scripting (XSS) and CSRF?"
    ],
    "Software Developer": [
        "For a Software Developer role: Walk me through how you design a clean, scalable RESTful API with proper HTTP status codes, versioning, and error payloads.",
        "Software Developer question: Explain the SOLID principles and share an example of how you used one to refactor code for better testability.",
        "As a Software Developer: How do you write unit and integration tests, and what strategies do you use for mocking external dependencies like databases?",
        "Software Developer question: Describe your end-to-end Git workflow when working with teammates on a major feature branch and resolving conflicts."
    ],
    "Data Analyst": [
        "As a candidate for Data Analyst: Explain your step-by-step process for Exploratory Data Analysis (EDA) on an unfamiliar and incomplete dataset.",
        "For a Data Analyst role: When would you use the SQL `HAVING` clause rather than the `WHERE` clause? Provide a practical scenario.",
        "Data Analyst question: How do you handle missing values or extreme outliers in your data without introducing unwanted analytical bias?",
        "As a Data Analyst: Describe how you present technical metrics and analytical dashboards to non-technical stakeholders to drive actionable decisions."
    ],
    "Computer Science Student": [
        "As a Computer Science Student: Explain the difference between a process and a thread, including how memory and resources are allocated.",
        "CS Student question: How does virtual memory work in modern operating systems, and what steps occur when a page fault happens?",
        "CS Student question: Compare the time and space complexity trade-offs of using an Array versus a Singly Linked List for frequent insertions and searches.",
        "For a CS Student: Explain the TCP three-way handshake and contrast TCP's reliability mechanisms with UDP."
    ],
    "General": [
        "Explain an important technical concept you have mastered, and explain how you would teach it to a new junior teammate.",
        "Describe a complex project you worked on recently: What was your specific responsibility, and how did you overcome the hardest obstacle?",
        "How do you approach learning a new programming language or framework under a tight deadline?"
    ]
}

# ============================================================================
# HR, APTITUDE, CODING BANKS (Extended to avoid repetition)
# ============================================================================

HR_MCQ_BANK = [
    {"question": "A teammate disagrees with your implementation approach during code review. What is the best initial step?", "options": ["Ignore their comment and merge anyway", "Ask questions to understand their reasoning and discuss the technical trade-offs constructively", "Escalate immediately to the executive team", "Stop contributing to the pull request"], "correct_index": 1, "topic": "Team Collaboration", "explanation": "Constructive discussions on technical trade-offs lead to better software and stronger team rapport."},
    {"question": "When asked about a weakness in an interview, you should...", "options": ["Claim you have zero weaknesses", "Share a real area for growth and explain the proactive steps you are taking to improve", "Blame your former team or university", "Refuse to answer personal questions"], "correct_index": 1, "topic": "Self Awareness", "explanation": "Demonstrating self-awareness and active growth shows professional maturity."},
    {"question": "Which structure is best suited for delivering clear, compelling answers to behavioral interview questions?", "options": ["STAR: Situation, Task, Action, Result", "A single-word answer", "Reciting random technical keywords", "Asking the interviewer to answer first"], "correct_index": 0, "topic": "STAR Method", "explanation": "STAR provides a structured, evidence-based format highlighting your personal contributions."},
    {"question": "You realize you will miss an agreed project deadline due to an unexpected blocker. What should you do?", "options": ["Wait until the deadline has passed and apologize", "Proactively notify your team and manager early, explain the blocker, and propose a revised timeline", "Hide the blocker and rush buggy code into production", "Abandon the project"], "correct_index": 1, "topic": "Accountability", "explanation": "Early communication allows teams to re-prioritize or provide support before deadlines fail."},
    {"question": "When explaining a team project, how can you best demonstrate your contribution?", "options": ["Claim sole credit for the entire team's achievements", "Clearly distinguish between team goals and your specific actions, responsibilities, and outcomes", "Downplay the project's significance", "Focus exclusively on negative teammate conflicts"], "correct_index": 1, "topic": "Communication & Ownership", "explanation": "Clear ownership highlights your personal impact while demonstrating respect for teamwork."}
]

HR_TEXT_BANK = [
    "Tell me about a time you encountered a significant roadblock in a project or assignment. How did you resolve it?",
    "Describe a situation where you had to quickly learn a technology you were unfamiliar with. What was your learning strategy?",
    "Tell me about a time you received critical feedback on your work. How did you react and what changes did you make?",
    "Walk me through a project where you collaborated with others. What was your role, and how did you resolve any differences of opinion?",
    "Why are you interested in this specific role, and how have your past experiences prepared you for it?"
]

APTITUDE_MCQ_BANK = [
    {"question": "A server's CPU usage increases from 40% to 50%. What is the percentage increase in CPU usage?", "options": ["10%", "20%", "25%", "30%"], "correct_index": 2, "topic": "Percentages", "explanation": "Increase = (50 - 40) / 40 * 100 = 10 / 40 * 100 = 25%."},
    {"question": "A team of 4 developers completes a module in 6 days. How many days would 6 developers take at the same rate?", "options": ["3 days", "4 days", "5 days", "2 days"], "correct_index": 1, "topic": "Work & Time", "explanation": "Total developer-days = 4 * 6 = 24. With 6 developers: 24 / 6 = 4 days."},
    {"question": "What is the next number in the sequence: 3, 7, 15, 31, __?", "options": ["47", "55", "63", "64"], "correct_index": 2, "topic": "Number Series", "explanation": "Each term is (previous * 2) + 1: 31 * 2 + 1 = 63."},
    {"question": "An API processes 1,800 requests per minute. How many requests does it process per second?", "options": ["18", "25", "30", "60"], "correct_index": 2, "topic": "Rates & Speed", "explanation": "1,800 requests / 60 seconds = 30 requests per second."},
    {"question": "A dataset contains 120 positive samples and 80 negative samples. What percentage of the dataset is positive?", "options": ["40%", "50%", "60%", "75%"], "correct_index": 2, "topic": "Ratios & Percentages", "explanation": "120 / (120 + 80) = 120 / 200 = 60%."},
    {"question": "If a pipeline transfers 450 MB of data in 15 seconds, what is its average transfer speed?", "options": ["25 MB/s", "30 MB/s", "35 MB/s", "45 MB/s"], "correct_index": 1, "topic": "Speed Calculation", "explanation": "450 / 15 = 30 MB/s."}
]

APTITUDE_TEXT_BANK = [
    "An algorithm's runtime increases from 200 ms to 350 ms after adding new features. Show your step-by-step math to calculate the percentage slowdown.",
    "A cloud database charges ₹0.05 per thousand read queries and ₹0.20 per thousand write queries. Show how you calculate the daily cost for 2 million reads and 500,000 writes.",
    "Explain how you would estimate the storage required for storing 10 million user records, each averaging 1.5 KB in size.",
    "A web server handles 300 requests/sec with an average latency of 50 ms. Explain how you would verify if current server capacity is sufficient under a 3x traffic spike."
]

CODING_MCQ_BANK = [
    {"question": "What is the output of `bool([])` in Python?", "options": ["True", "False", "None", "Raises an error"], "correct_index": 1, "topic": "Python Truthiness", "explanation": "Empty collections like empty lists, sets, and dicts evaluate to `False` in boolean contexts."},
    {"question": "Which data structure operates on a Last-In, First-Out (LIFO) basis?", "options": ["Queue", "Stack", "Priority Queue", "Deque"], "correct_index": 1, "topic": "Data Structures", "explanation": "A stack pushes and pops elements from the top, following LIFO order."},
    {"question": "What is the time complexity of binary search on a sorted array of size n?", "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"], "correct_index": 1, "topic": "Search Algorithms", "explanation": "Binary search halves the search space in each step, taking O(log n) time."},
    {"question": "Which Python keyword is used to handle exceptions gracefully?", "options": ["catch", "except", "trap", "rescue"], "correct_index": 1, "topic": "Exception Handling", "explanation": "Python uses `try` and `except` blocks to handle exceptions."},
    {"question": "In Python, which built-in function returns both the index and value when iterating over a list?", "options": ["index()", "enumerate()", "zip()", "range()"], "correct_index": 1, "topic": "Python Iteration", "explanation": "`enumerate(iterable)` yields pairs of `(index, item)`."},
    {"question": "What will `len(set([1, 2, 2, 3, 3, 3]))` return in Python?", "options": ["6", "3", "1", "TypeError"], "correct_index": 1, "topic": "Sets", "explanation": "Sets only store distinct unique elements, so `{1, 2, 3}` has length 3."}
]

CODING_TEXT_BANK = [
    "Write out or describe an algorithm to reverse a string in-place or without using built-in reverse functions.",
    "Explain how you would find the second highest number in an unsorted list in a single pass O(n) time.",
    "Describe your approach to detect whether a given string is a palindrome, ignoring casing and spaces.",
    "How would you check whether two strings are anagrams of each other? Explain the time complexity of your approach.",
    "Explain how you would remove duplicate values from a list while preserving the original insertion order."
]

# ============================================================================
# DYNAMIC GENERATORS (Guarantees zero duplicates even after many sessions)
# ============================================================================

def generate_dynamic_resume_question(skill, used_questions, mode="MCQ"):
    """
    Generate dynamic resume questions that won't collide with previous questions.
    """
    templates = [
        ("Architecture", "In your resume, you listed {skill}. When architecting a real-world project with {skill}, how do you organize module boundaries and separate concerns?"),
        ("Error Handling", "Based on {skill} mentioned in your resume: What strategy do you employ for comprehensive error logging and graceful failure recovery?"),
        ("Scaling", "Your resume features {skill}. How do you optimize memory and throughput when scaling a {skill} system to handle high concurrent usage?"),
        ("Testing", "Referencing your resume experience with {skill}: What level of automated unit, integration, and regression testing do you implement?"),
        ("Security", "Your resume notes experience with {skill}. What essential security best practices (e.g., input sanitization, credential management) do you adhere to when using {skill}?")
    ]
    random.shuffle(templates)
    for tag, tmpl in templates:
        q_text = tmpl.format(skill=skill)
        norm = normalize_question(q_text)
        if norm not in used_questions:
            used_questions.add(norm)
            if mode == "MCQ":
                return {
                    "question": q_text,
                    "options": [
                        f"Implement clear layer separation, dedicated error boundaries, and proactive validation",
                        f"Bundle all database and presentation code into a single monolithic script",
                        f"Disable exception logging to maximize runtime throughput",
                        f"Hardcode all application configurations directly in source files"
                    ],
                    "correct_index": 0,
                    "topic": f"Resume: {skill} {tag}",
                    "explanation": f"Professional production {skill} implementations prioritize modularity, error recovery, and maintainable boundaries.",
                    "category": "resume",
                    "badge": f"Resume: {skill}"
                }
            else:
                return {
                    "question": q_text,
                    "options": [],
                    "correct_index": None,
                    "topic": f"Resume: {skill} ({tag})",
                    "explanation": "",
                    "category": "resume",
                    "badge": f"Resume: {skill}"
                }
    return None

def generate_dynamic_role_question(role, interview_type, used_questions, mode="MCQ"):
    """
    Generate dynamic role questions that won't collide with previous questions.
    """
    scenarios = [
        ("Concurrency & Locking", f"As a {role}: How do you prevent race conditions and maintain state consistency during concurrent read/write operations?"),
        ("Incident Response", f"In a {role} position: A critical production service experiences a sudden 500-error spike. Walk through your triage and root-cause analysis workflow."),
        ("Refactoring", f"As a {role}: When inheriting legacy code with high technical debt, how do you safely refactor critical modules without breaking existing user flows?"),
        ("API Contracts", f"For a {role} role: What principles do you follow when designing backward-compatible API contracts for distributed clients?"),
        ("Monitoring & Metrics", f"As a {role}: What key health metrics and telemetry (latency, error rate, memory) do you monitor to guarantee system reliability?")
    ]
    random.shuffle(scenarios)
    for tag, q_text in scenarios:
        norm = normalize_question(q_text)
        if norm not in used_questions:
            used_questions.add(norm)
            if mode == "MCQ":
                return {
                    "question": q_text,
                    "options": [
                        "Use atomic transactions, proper isolation levels, or immutable state structures",
                        "Rely entirely on client-side retry loops without server locking",
                        "Ignore concurrency and assume requests arrive strictly sequentially",
                        "Disable all logging to prevent I/O disk contention"
                    ],
                    "correct_index": 0,
                    "topic": f"Role: {role} - {tag}",
                    "explanation": f"In a {role} capacity, robust system design requires deterministic concurrency control and observable telemetry.",
                    "category": "role",
                    "badge": f"Role: {role}"
                }
            else:
                return {
                    "question": q_text,
                    "options": [],
                    "correct_index": None,
                    "topic": f"Role: {role} ({tag})",
                    "explanation": "",
                    "category": "role",
                    "badge": f"Role: {role}"
                }
    return None

# ============================================================================
# MASTER QUESTION GENERATION ENGINE
# ============================================================================

def get_questions(interview_type, answer_mode, role, difficulty, resume_text, job_description, candidate_name, db_path):
    """
    Master function:
    1. Fetches previous questions for this candidate/session to PREVENT repetition.
    2. Extracts resume skills & projects.
    3. Tries AI generation with anti-repetition prompt if API key exists.
    4. Otherwise generates balanced Resume-Based (2-3) and Role-Based (2-3) questions locally.
    5. Tags each question with category: 'resume' or 'role' and badges.
    """
    used_questions = get_previously_asked_questions(db_path, candidate_name=candidate_name)
    resume_data = extract_resume_details(resume_text)
    detected_skills = resume_data["skills"]
    detected_projects = resume_data["projects"]

    # 1. Try AI generation if API key is configured
    ai_result = try_ai_generation(
        interview_type=interview_type,
        answer_mode=answer_mode,
        role=role,
        difficulty=difficulty,
        resume_text=resume_text,
        detected_skills=detected_skills,
        job_description=job_description,
        used_questions=used_questions
    )
    if ai_result and len(ai_result) >= 5:
        return ai_result[:5], "AI-generated (Dual Resume + Role)"

    # 2. Local Intelligent Generation
    selected_questions = []
    has_resume = bool(detected_skills or resume_text.strip())

    # How many resume questions vs role questions?
    if has_resume:
        resume_target = 3 if len(detected_skills) >= 2 else 2
        role_target = 5 - resume_target
    else:
        resume_target = 0
        role_target = 5

    # A) Gather Resume-Based Questions
    if resume_target > 0:
        skill_pool = list(detected_skills) if detected_skills else ["Python", "Communication"]
        random.shuffle(skill_pool)

        if answer_mode == "MCQ":
            for s in skill_pool:
                if len(selected_questions) >= resume_target:
                    break
                bank = RESUME_MCQ_BANK.get(s, [])
                for q in bank:
                    norm = normalize_question(q["question"])
                    if norm not in used_questions:
                        used_questions.add(norm)
                        q_copy = dict(q)
                        q_copy["category"] = "resume"
                        q_copy["badge"] = f"Resume: {s}"
                        selected_questions.append(q_copy)
                        break

            # If still need resume questions, generate dynamically
            while len(selected_questions) < resume_target:
                s = random.choice(skill_pool) if skill_pool else "Technical"
                dyn = generate_dynamic_resume_question(s, used_questions, mode="MCQ")
                if dyn:
                    selected_questions.append(dyn)
                else:
                    break
        else: # Written mode
            for s in skill_pool[:resume_target]:
                proj_ref = detected_projects[0] if detected_projects else f"your {s} projects"
                for tmpl in RESUME_TEXT_BANK["default"]:
                    q_text = tmpl.format(skill=s, project_ref=proj_ref)
                    norm = normalize_question(q_text)
                    if norm not in used_questions:
                        used_questions.add(norm)
                        selected_questions.append({
                            "question": q_text,
                            "options": [],
                            "correct_index": None,
                            "topic": f"Resume: {s}",
                            "explanation": "",
                            "category": "resume",
                            "badge": f"Resume: {s}"
                        })
                        break
                if len(selected_questions) >= resume_target:
                    break

            # If still short, generate dynamic resume questions
            while len(selected_questions) < resume_target:
                s = random.choice(skill_pool) if skill_pool else "Software Engineering"
                dyn = generate_dynamic_resume_question(s, used_questions, mode="Written")
                if dyn:
                    selected_questions.append(dyn)
                else:
                    break

    # B) Gather Role-Based Questions
    role_key = role if role in ROLE_MCQ_BANK else "Software Developer"
    if role not in ROLE_MCQ_BANK:
        # Check closest match
        for rk in ROLE_MCQ_BANK:
            if rk.lower() in role.lower():
                role_key = rk
                break

    needed_role = 5 - len(selected_questions)

    if answer_mode == "MCQ":
        # First check interview type specific pools if HR, Aptitude, Coding
        type_bank = []
        if interview_type == "HR":
            type_bank = HR_MCQ_BANK
        elif interview_type == "Aptitude":
            type_bank = APTITUDE_MCQ_BANK
        elif interview_type == "Coding":
            type_bank = CODING_MCQ_BANK
        else: # Technical
            type_bank = ROLE_MCQ_BANK.get(role_key, ROLE_MCQ_BANK["Software Developer"])

        shuffled_bank = list(type_bank)
        random.shuffle(shuffled_bank)

        for q in shuffled_bank:
            if len(selected_questions) >= 5:
                break
            norm = normalize_question(q["question"])
            if norm not in used_questions:
                used_questions.add(norm)
                q_copy = dict(q)
                q_copy["category"] = "role"
                q_copy["badge"] = f"Role: {role}"
                selected_questions.append(q_copy)

        # If more needed, also check role technical bank
        if len(selected_questions) < 5 and role_key in ROLE_MCQ_BANK:
            for q in ROLE_MCQ_BANK[role_key]:
                if len(selected_questions) >= 5:
                    break
                norm = normalize_question(q["question"])
                if norm not in used_questions:
                    used_questions.add(norm)
                    q_copy = dict(q)
                    q_copy["category"] = "role"
                    q_copy["badge"] = f"Role: {role}"
                    selected_questions.append(q_copy)

        # Dynamic role questions if exhausted
        while len(selected_questions) < 5:
            dyn = generate_dynamic_role_question(role, interview_type, used_questions, mode="MCQ")
            if dyn:
                selected_questions.append(dyn)
            else:
                break

    else: # Written mode
        type_bank = []
        if interview_type == "HR":
            type_bank = HR_TEXT_BANK
        elif interview_type == "Aptitude":
            type_bank = APTITUDE_TEXT_BANK
        elif interview_type == "Coding":
            type_bank = CODING_TEXT_BANK
        else:
            type_bank = ROLE_TEXT_BANK.get(role_key, ROLE_TEXT_BANK["Software Developer"])

        shuffled_bank = list(type_bank)
        random.shuffle(shuffled_bank)

        for q_text in shuffled_bank:
            if len(selected_questions) >= 5:
                break
            norm = normalize_question(q_text)
            if norm not in used_questions:
                used_questions.add(norm)
                selected_questions.append({
                    "question": q_text,
                    "options": [],
                    "correct_index": None,
                    "topic": f"Role: {role}",
                    "explanation": "",
                    "category": "role",
                    "badge": f"Role: {role}"
                })

        # If still needed, pull from role text bank
        if len(selected_questions) < 5 and role_key in ROLE_TEXT_BANK:
            for q_text in ROLE_TEXT_BANK[role_key]:
                if len(selected_questions) >= 5:
                    break
                norm = normalize_question(q_text)
                if norm not in used_questions:
                    used_questions.add(norm)
                    selected_questions.append({
                        "question": q_text,
                        "options": [],
                        "correct_index": None,
                        "topic": f"Role: {role}",
                        "explanation": "",
                        "category": "role",
                        "badge": f"Role: {role}"
                    })

        # Dynamic fallback
        while len(selected_questions) < 5:
            dyn = generate_dynamic_role_question(role, interview_type, used_questions, mode="Written")
            if dyn:
                selected_questions.append(dyn)
            else:
                break

    # Final shuffle so resume and role questions are nicely interleaved
    random.shuffle(selected_questions)
    source_label = "Dual Engine (Resume-Based + Role-Based)" if has_resume else "Role-Based Intelligent Engine"
    return selected_questions[:5], source_label

def try_ai_generation(interview_type, answer_mode, role, difficulty, resume_text, detected_skills, job_description, used_questions):
    """
    Generate questions using Gemini AI (or OpenAI) with strict anti-repetition & resume+role partitioning.
    """
    # 1. Try Google Gemini with the configured API key
    try:
        import gemini_client
        gemini_res = gemini_client.gemini_generate_questions(
            interview_type=interview_type,
            answer_mode=answer_mode,
            role=role,
            difficulty=difficulty,
            resume_text=resume_text,
            detected_skills=detected_skills,
            job_description=job_description,
            used_questions=used_questions
        )
        if gemini_res and len(gemini_res) >= 4:
            return gemini_res
    except Exception as gemini_err:
        print("Gemini generation attempt failed, checking fallback:", gemini_err)

    # 2. Try OpenAI if configured
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=25.0)

        # Provide a sample of previously asked questions to avoid
        used_sample = list(used_questions)[:25]
        used_clause = ""
        if used_sample:
            used_clause = f"CRITICAL: The candidate has already been asked questions similar to these in past sessions. DO NOT repeat or closely rephrase any of them: {json.dumps(used_sample)}"

        has_resume = bool(detected_skills or (resume_text and resume_text.strip()))
        structure_instruction = (
            "Create exactly 5 practical interview questions.\n"
            "- Exactly 2 or 3 questions MUST BE STRICTLY RESUME-BASED (evaluating specific skills, projects, and frameworks found in the candidate's resume). For these, set 'category': 'resume' and 'badge': 'Resume: <Skill>'.\n"
            "- Exactly 2 or 3 questions MUST BE STRICTLY ROLE-BASED (evaluating core competencies and real-world responsibilities of the target job role). For these, set 'category': 'role' and 'badge': 'Role: <Role>'.\n"
        ) if has_resume else (
            f"Create exactly 5 practical interview questions STRICTLY ROLE-BASED for the target role: {role}. For all questions, set 'category': 'role' and 'badge': 'Role: {role}'.\n"
        )

        schema_hint = (
            "Return ONLY a valid JSON array of 5 objects. "
            "For MCQ, each object must have: question, options (array of exactly 4 strings), correct_index (0-3), topic, explanation, category ('resume' or 'role'), badge. "
            "For Written, each object must have: question, options: [], correct_index: null, topic, explanation: '', category ('resume' or 'role'), badge."
        )

        prompt = f"""You are a senior hiring manager and technical interviewer.
Target Role: {role}
Interview Type: {interview_type}
Difficulty Level: {difficulty}
Answer Mode: {answer_mode}
Detected Resume Skills: {', '.join(detected_skills) if detected_skills else 'None'}
Resume Text: {resume_text[:4000]}
Job Description: {job_description[:2000]}

{structure_instruction}
{used_clause}
{schema_hint}

Make all questions engaging, specific, and realistic for learning. No generic fluff."""

        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You create fair, non-repetitive interview practice content. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        content = response.choices[0].message.content.strip()
        # Clean any markdown code fences if returned
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

        result = json.loads(content)
        clean = []
        for item in result:
            if not isinstance(item, dict) or not item.get("question"):
                continue
            q_text = str(item["question"])[:1000]
            norm = normalize_question(q_text)
            if norm in used_questions:
                continue  # Skip any repeated question!
            used_questions.add(norm)

            cat = item.get("category", "role")
            badge = item.get("badge", f"{cat.capitalize()}: {role}")

            if answer_mode == "MCQ":
                opts = item.get("options", [])
                c_idx = item.get("correct_index")
                if len(opts) != 4 or not isinstance(c_idx, int) or c_idx not in range(4):
                    continue
                clean.append({
                    "question": q_text,
                    "options": [str(o)[:300] for o in opts],
                    "correct_index": c_idx,
                    "topic": str(item.get("topic", interview_type))[:100],
                    "explanation": str(item.get("explanation", ""))[:600],
                    "category": cat,
                    "badge": badge
                })
            else:
                clean.append({
                    "question": q_text,
                    "options": [],
                    "correct_index": None,
                    "topic": str(item.get("topic", interview_type))[:100],
                    "explanation": "",
                    "category": cat,
                    "badge": badge
                })
        return clean if len(clean) >= 4 else None
    except Exception as exc:
        print("Optional AI question generation unavailable; using built-in dual engine:", exc)
        return None
