# InsureChain VoiceGuard — Flutter Mobile Application

## 1. Overview & Purpose
This folder contains the mobile application for **InsureChain VoiceGuard**, built with Flutter for **VORTEXA 3.0 (Problem Statement B-02: Policy-Aware Insurance Claims Workflow)**.

The mobile client delivers an accessible, voice-first, touch-optimized experience supporting all three primary user roles:
1. **Customer**
2. **Insurance Agent**
3. **Approval Authority**

The mobile app ensures seamless on-the-go interactions, such as field recording of sales conversations by agents with explicit consent, transparent promise verification and policy confirmation by customers, and rapid claim inspection by authorities.

---

## 2. Technology Stack
- **Framework**: Flutter (Stable channel) with Dart null safety
- **Design System**: Material 3 styled with the project fintech theme (Navy, Off-white, Violet, Teal)
- **State Management**: Riverpod (`flutter_riverpod`)
- **Navigation & Routing**: GoRouter (`go_router`) with role-aware route redirects
- **Networking**: Dio (`dio`) with interceptors for JWT token injection and error handling
- **Secure Storage**: Flutter Secure Storage (`flutter_secure_storage`) for hardware-backed token and session persistence
- **Audio & Media**:
  - `record` for microphone capture with real-time amplitude/waveform streaming
  - `audioplayers` for sales conversation playback and ElevenLabs spoken explanations
- **Document & Image Capture**: `file_picker` and `image_picker`
- **Notifications**: `flutter_local_notifications` for simulated policy renewal and claim-state alerts

---

## 3. Supported Platforms
- **Primary Hackathon Target**: Android (optimized for modern Android devices).
- **Architecture**: Structured cleanly according to clean architecture/feature-first patterns to maintain full compatibility for future iOS support without native modifications.

---

## 4. Role-Specific Capabilities & Modules

### 4.1 Customer Experience
- **Policy Portfolio**: Real-time display of simulated active policies, coverage terms, waiting periods, and expiry dates.
- **Vaada Sales Verification**:
  - Review pending registrations (`PENDING_CONFIRMATION`).
  - Native audio player to listen to the sales recording.
  - Interactive transcript with highlighted promises.
  - Dedicated Contradictions view comparing agent claims with exact policy clauses and page numbers.
  - Affirmative customer confirmation or decline action.
- **Mobile Claim Filing**:
  - Step-by-step guided submission for Vehicle, Hospitalization, and Generic categories.
  - Direct camera and file attachment for invoices, discharge summaries, and incident photos.
  - Completeness validation feedback.
- **Voice Assistant**:
  - Voice-enabled query interface powered by ElevenLabs for policy terms, limits, and claim progress updates.

### 4.2 Insurance Agent Experience
- **Scheme Catalog**: Instant search and selection of simulated insurance products.
- **Consent-Gated Sales Recording**:
  - Prominent consent confirmation dialog prior to opening microphone stream.
  - Visible recording banner, animated amplitude waveform, and manual stop action.
  - Automatic off-chain upload and ElevenLabs transcription initiation.
- **Customer Onboarding**:
  - Entry of synthetic customer contact and declaration data.
  - Upload of simulated proof documents.
  - Submission for customer confirmation.
- **Promise Review**:
  - Immediate review of transcription and preliminary promise-versus-policy alignment.

### 4.3 Approval Authority Mobile Workbench
- **Claims Overview**: High-level KPI cards and filtered list of submitted and flagged claims.
- **Quick Evaluation**:
  - Rule evaluation results (passed, failed, and above-limit calculations).
  - High-priority warnings (duplicate incident candidates, document manipulation alerts).
  - Decision actions: Request Evidence, Approve, or Reject with recorded reason.
- **Spoken Summaries**: Audio playback of generated decision explanations.

---

## 5. Security & Networking Constraints
- **Zero Direct Database Connections**: Connects strictly to the centralized FastAPI backend over HTTPS.
- **Token Security**: JWT tokens stored exclusively in `FlutterSecureStorage`.
- **Sensitive Data Isolation**: No personal customer data, medical information, or private keys stored in plaintext.

---

## 6. Future Development Roadmap
- Configure Android permissions in `android/app/src/main/AndroidManifest.xml` (Microphone, Storage, Camera, Internet).
- Establish folder structure (`lib/core/`, `lib/features/`, `lib/shared/`).
- Implement the Dio API client and Riverpod authentication providers.
- Build UI components adhering to the Material 3 design tokens.
