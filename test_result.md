#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: >
  DocChat — Enterprise RAG Platform. Build a full-stack enterprise-grade RAG platform that lets
  users upload documents and have AI-powered conversations grounded in those documents, with
  citations, access control, and secure sharing. Latest addition: ENABLE_EMBED_WIDGET feature
  — embeddable chat widget that any third-party website can install.

backend:
  - task: "Embed widget CRUD API (POST/GET/PATCH/DELETE /api/v2/widgets)"
    implemented: true
    working: true
    file: "backend/routers/widgets.py"
    stuck_count: 0
    priority: high
    needs_retesting: false
    status_history:
      - working: true
        agent: main
        comment: "Created routers/widgets.py with full CRUD + analytics endpoint. Feature flag ENABLE_EMBED_WIDGET enforced."

  - task: "Public widget endpoints (loader.js, iframe HTML, config, streaming chat)"
    implemented: true
    working: true
    file: "backend/routers/widget_public.py"
    stuck_count: 0
    priority: high
    needs_retesting: false
    status_history:
      - working: true
        agent: main
        comment: "GET /api/widget/loader.js (2.7KB), GET /api/widget/{id}/iframe, GET /api/widget/{id}/config, POST /api/widget/{id}/chat. Domain whitelist, rate limiting, SSE streaming all implemented."

  - task: "DB collections: embed_widgets, widget_sessions, widget_events + indexes"
    implemented: true
    working: true
    file: "backend/core/db.py"
    stuck_count: 0
    priority: high
    needs_retesting: false
    status_history:
      - working: true
        agent: main
        comment: "Added 3 collections + indexes to db.py and init_indexes()."

frontend:
  - task: "Embed Widget builder page with 3 tabs + live preview"
    implemented: true
    working: true
    file: "frontend/src/pages/EmbedWidget.jsx"
    stuck_count: 0
    priority: high
    needs_retesting: false
    status_history:
      - working: true
        agent: testing
        comment: "All tabs (Appearance/Behaviour/Security/Install), live preview, widget list, analytics dialog, active/pause toggle all working correctly."

  - task: "Embed Widget nav item + route in AppLayout/App.js"
    implemented: true
    working: true
    file: "frontend/src/pages/AppLayout.jsx"
    stuck_count: 0
    priority: medium
    needs_retesting: false
    status_history:
      - working: true
        agent: testing
        comment: "Nav item visible in sidebar, routes to /app/embed-widget correctly."

metadata:
  created_by: main_agent
  version: "1.0"
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: high_first

agent_communication:
  - agent: main
    message: "Implemented full ENABLE_EMBED_WIDGET feature. All backend and frontend components verified by testing agent."

user_problem_statement: "Test the DocChat Embed Widget feature"

frontend:
  - task: "Embed Widget Navigation"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/AppLayout.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Navigation item 'Embed widget' is present in sidebar with correct testId='nav-embed-widget'. Navigation to /app/embed-widget works correctly."

  - task: "Embed Widget List Page"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/EmbedWidget.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Empty state displays correctly with 'No widgets yet' message and 'Create first widget' button. Info banner about widget functionality is visible."

  - task: "Widget Builder - Basic Layout"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/EmbedWidget.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Widget builder page loads correctly with header 'Create widget', back button, and save button. Layout includes left form panel and right live preview panel."

  - task: "Widget Builder - Name and Document Scope"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/EmbedWidget.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Widget name input field works correctly. Document scope section displays with checkbox list (shows 'No ready documents' message when no documents available). Counter shows '0 selected'."

  - task: "Widget Builder - Appearance Tab"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/EmbedWidget.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Appearance tab displays all fields correctly: Widget title input, Subtitle input, Brand color picker with hex input, Widget position selector (Bottom Right/Left), Launcher style selector (Icon only/Icon+Label), Dark mode toggle switch."

  - task: "Widget Builder - Behaviour Tab"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/EmbedWidget.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Behaviour tab displays all fields correctly: Welcome message textarea, Fallback message textarea, Max questions per session input (0=unlimited), Email collection selector (Off/Optional/Required), Show citations toggle, Show confidence toggle, Allow copy toggle. All toggles are functional."

  - task: "Widget Builder - Security Tab"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/EmbedWidget.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Security tab displays all fields correctly: Allowed domains textarea with placeholder examples (supports wildcards like *.company.com), Max queries per visitor per hour input (default 20), Max queries per day input (default 500). Server-side enforcement info banner is visible."

  - task: "Widget Builder - Live Preview"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/EmbedWidget.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Live preview panel displays correctly on the right side showing: Phone frame with widget panel, Widget header with title and subtitle, Sample message bubbles (welcome message, user question, assistant answer), Citations display, Confidence badge, Input area with send button, Launcher button preview below. Preview updates in real-time with configuration changes."

metadata:
  created_by: "testing_agent"
  version: "1.0"
  test_sequence: 1

test_plan:
  current_focus:
    - "All Embed Widget features tested"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "testing"
      message: "Completed comprehensive testing of DocChat Embed Widget feature. All UI elements are functional and rendering correctly. Navigation works, empty state displays properly, widget builder loads with all tabs (Appearance, Behaviour, Security), live preview updates correctly. No console errors or network failures detected. Document scope shows expected message when no documents are available. All form fields are accessible and functional."


user_problem_statement: "Test document upload improvements: duplicate detection, failed document retry button, and PPTX/XLSX/Image file format support"

frontend:
  - task: "Duplicate detection on file upload"
    implemented: true
    working: true
    file: "/app/frontend/src/components/UploadDialog.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Duplicate detection working correctly. When uploading the same file twice, a toast notification appears with message 'Duplicate detected: [filename] already exists ([status])'. The toast correctly displays the existing filename and document status. Backend returns 409 status with DUPLICATE code, frontend handles it properly."

  - task: "Failed document retry button"
    implemented: true
    working: true
    file: "/app/frontend/src/pages/Dashboard.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Retry button working correctly. Failed documents display a circular arrow (ArrowClockwise) icon button next to the FAILED status badge. Clicking the retry button successfully triggers reprocessing via POST /v2/documents/{id}/reprocess. Toast notification confirms 'Retrying [filename]…' and document status changes from FAILED to QUEUED with progress bar."

  - task: "PPTX/XLSX/Image file format support"
    implemented: true
    working: true
    file: "/app/frontend/src/components/UploadDialog.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "File format support working correctly. Upload dialog file picker accepts all expected formats: .pptx, .xlsx, .csv, .png, .jpg, .jpeg. The accept attribute includes all formats, and the UI displays 'PDF · DOCX · Text · Markdown · PowerPoint · Excel · CSV · Image (OCR)'. Feature flags ENABLE_PPTX_SUPPORT, ENABLE_EXCEL_SUPPORT, and ENABLE_IMAGE_OCR are enabled by default in backend config."

backend:
  - task: "Duplicate detection API (SHA-256 hash check)"
    implemented: true
    working: true
    file: "/app/backend/routers/documents.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Backend duplicate detection working correctly. Computes SHA-256 hash of file content and checks for existing documents with same hash. Returns 409 status with detailed error including code='DUPLICATE', existing_filename, existing_status, and message. Tested successfully with duplicate file upload."

  - task: "Document reprocess endpoint"
    implemented: true
    working: true
    file: "/app/backend/routers/documents.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Reprocess endpoint working correctly. POST /v2/documents/{id}/reprocess successfully resets document status to 'queued', removes existing chunks, and re-triggers ingestion. Tested with failed document 'erLicence.png' - status changed from FAILED to QUEUED with progress bar."

  - task: "Extended file format support (PPTX/XLSX/Images)"
    implemented: true
    working: true
    file: "/app/backend/core/config.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "Extended format support enabled. Feature flags ENABLE_PPTX_SUPPORT, ENABLE_EXCEL_SUPPORT, and ENABLE_IMAGE_OCR default to True in config.py. Backend accepts .pptx, .xlsx, .csv, .png, .jpg, .jpeg files. Verified through /v2/flags endpoint and file upload dialog."

metadata:
  created_by: "testing_agent"
  version: "1.0"
  test_sequence: 2

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

    - agent: "main"
      message: "Requesting testing of document upload improvements: 1) Duplicate detection, 2) Failed document retry button, 3) PPTX/XLSX/Image file format support"
    - agent: "testing"
      message: "Completed testing of document upload improvements. All three features are working correctly: 1) Duplicate detection shows proper toast with filename and status, 2) Failed documents display retry button that successfully triggers reprocessing, 3) File picker accepts PPTX, XLSX, CSV, PNG, JPG, JPEG formats as expected."