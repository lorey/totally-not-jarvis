import re


def extract_list(text):
    return text.replace(', and', ', ').replace('and ', ', ').split(', ')

def extract_emails(text):
    # extract emails
    email_regex = re.compile('[\w\.-]+@[\w\.-]+')
    emails = email_regex.findall(text)
    return emails