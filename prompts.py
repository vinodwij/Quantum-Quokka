SCHEMA_DESCRIPTION = """
Employee(ID, Name, Title, Email, PhoneNumber, Status),
Company(ID, Name, SectorCategory, OwnerID, Description),
Vendor(ID, Description, ServiceCategory, ContactPersonName, ContactPersonPhoneNumber, ContactPersonEmail),
Demand(ID, Name, Description, ReceivedDate, Status, GoLiveDate, AbandonmentReason, Phase, CompanyID, DeliveryDomain, ServiceCategory, CompanyPriority, CompanyValueDescription, CompanyValueClassification, ImplementationComplexity, ImplementationCostEstimate, ImplementationDuration, ProjectManagerID, OwnerID, VendorID, DTOwnerID),
DAB(DemandID, Date, Status, Notes),
Milestone(DemandID, Date, Description, AchievedOrNot),
Status(DemandID, Date, Description, UpdatedBy),
Proposal(DemandID, DateReceived, ProposalURL, ProposalStatus),
Material(DemandID, URL, MaterialDescription, DateAdded),
Meeting(DemandID, Date, Notes, RecordingURL),
Issues(EmployeeID, DemandID, TimeRaised, IssueDescription, Status, ResolutionDescription, ResolutionTime)
"""

SYSTEM_SQL = f"""
You are a SQL generation assistant. Given a user's question and the MySQL schema below,
generate a single valid `SELECT` query only (no explanations). Use exact table/column names.
Schema:
{SCHEMA_DESCRIPTION}
"""

SYSTEM_SUMMARY = """
You are a helpful assistant that, given a question, the SQL used, and its raw results (JSON),
summarizes the answer in clear English.
"""
