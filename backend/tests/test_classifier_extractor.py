import pytest

from app.models.enums import EmailCategory as C
from app.services.email_classifier.classifier import RuleBasedClassifier
from app.services.email_classifier.extractor import extract

clf = RuleBasedClassifier()


@pytest.mark.parametrize("subject,body,expected", [
    ("Your application for Backend Developer at ABC Technologies", "Thank you for applying. We have received your application and will review it shortly.", C.APPLICATION_CONFIRMATION),
    ("Interview Invitation — Python Developer", "We'd like to invite you for an interview next week.", C.INTERVIEW_INVITATION),
    ("Update on your application", "Unfortunately, we have decided to move forward with other candidates for this position.", C.REJECTION),
    ("Your application to Acme", "After careful consideration we are unable to move forward with your candidacy.", C.REJECTION),
    ("Your application to Acme", "trk=email_application_rejected_01", C.REJECTION),
    ("Next steps: technical assessment", "Please complete the coding challenge within 5 days. Thanks for applying to this role.", C.ASSESSMENT_INVITATION),
    ("Job offer from Globex", "We are pleased to offer you the position of Engineer.", C.JOB_OFFER),
    ("Your application is under review", "Our hiring team is reviewing your application.", C.UNDER_REVIEW),
    ("Your application was viewed", "The hiring team at Acme has viewed your application.", C.UNDER_REVIEW),
    ("Weekly job alert: 12 new jobs for you", "Backend roles near you", C.NOT_JOB_RELATED),
    ("50% off shoes", "Unfortunately this sale ends tonight. We are unable to extend it.", C.NOT_JOB_RELATED),
    ("Your account is under review", "Please verify your identity.", C.NOT_JOB_RELATED),
])
def test_classification(subject, body, expected):
    assert clf.classify("x@y.com", subject, body).category == expected


def test_extract_from_subject():
    e = extract("ABC Technologies Recruiting <jobs@abc.com>", "Your application for Backend Developer at ABC Technologies", "")
    assert (e.job_title, e.company) == ("Backend Developer", "ABC Technologies")


def test_extract_title_after_dash():
    assert extract("hr@abc.com", "Interview Invitation — Python Developer", "").job_title == "Python Developer"


def test_extract_company_from_sender_fallback():
    assert extract("Globex Careers <noreply@globex.com>", "Update on your application", "").company == "Globex"
    assert extract("no-reply@greenhouse.io", "Update", "").company is None


def test_extract_linkedin_confirmation_title_from_email_card():
    body = "Your application was sent to Hire Feed Software Engineer - E-Commerce (Remote) Hire Feed Pakistan View job"
    extracted = extract("LinkedIn <jobs-noreply@linkedin.com>", "Your application was sent to Hire Feed", body)
    assert (extracted.job_title, extracted.company) == ("Software Engineer - E-Commerce (Remote)", "Hire Feed")
