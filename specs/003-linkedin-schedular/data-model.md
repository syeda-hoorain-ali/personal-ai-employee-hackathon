# Data Model: Silver Tier LinkedIn Automation & Scheduling

## Overview
This document defines the data models for the LinkedIn automation and scheduling system based on the key entities identified in the feature specification.

## Entity: LinkedInPost
**Description**: Represents a LinkedIn post with content, schedule time, and posting status

**Attributes**:
- id: Unique identifier for the post
- content: String containing the post content
- scheduledTime: DateTime when the post is scheduled to be published
- actualPublishTime: DateTime when the post was actually published (nullable)
- status: Enum ("scheduled", "published", "failed", "pending")
- contentType: Enum ("announcement", "insight", "success", "testimonial")
- retryCount: Integer counter for failed post attempts
- failureReason: String describing reason for failure (nullable)

**Validation Rules**:
- content must not be empty
- scheduledTime must be in the future
- status must be one of the defined enum values

## Entity: ScheduleConfig
**Description**: Contains scheduling parameters including posting times and frequency

**Attributes**:
- postId: Reference to LinkedInPost.id
- daysOfWeek: Array of days when posts should be scheduled (e.g., ["Monday", "Thursday"])
- scheduledTimeOfDay: Time of day when scheduler should run (e.g., "12:00 PM")
- targetPublicationTime: Time of day when posts should be published (e.g., "6:00 PM")
- isActive: Boolean indicating if this schedule is active
- timeZone: String representing the timezone for scheduling

**Validation Rules**:
- daysOfWeek must contain valid day names
- scheduledTimeOfDay must be before targetPublicationTime
- isActive must be boolean

## Entity: BusinessContent
**Description**: Business-focused content that can be used for LinkedIn posts

**Attributes**:
- id: Unique identifier for the content
- companyName: String with the company name
- industry: String describing the industry
- topics: Array of topic strings related to the business
- tone: String describing the content tone ("professional", "casual", etc.)
- contentTypes: Array of allowed content types to generate
- creationDate: DateTime when the content configuration was created
- lastModified: DateTime when the content configuration was last updated

**Validation Rules**:
- companyName must not be empty
- industry must not be empty
- topics array must contain at least one topic
- contentTypes array must contain valid content type values

## Entity: ErrorLog
**Description**: Stores information about failed post attempts for error handling

**Attributes**:
- id: Unique identifier for the error log entry
- postId: Reference to LinkedInPost.id
- timestamp: DateTime when the error occurred
- errorMessage: String describing the error
- errorType: String categorizing the error type (e.g., "credential", "network", "api")
- notifiedUser: Boolean indicating if the user was notified of the error
- retryScheduled: Boolean indicating if a retry has been scheduled

**Validation Rules**:
- timestamp must be present
- errorType must be one of the defined types
- postId must reference an existing LinkedInPost

## Relationships
- LinkedInPost has one ScheduleConfig (one-to-one)
- BusinessContent can generate many LinkedInPost entries (one-to-many)
- ErrorLog references LinkedInPost (many-to-one)