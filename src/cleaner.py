from cleantext import clean

def clean_amharic(text):
    return clean(
        text,
        fix_unicode=True,
        to_ascii=False,
        no_line_breaks=True,
        lower=True,
        no_emoji=True,  
        replace_with_url="",
        replace_with_email="",
        replace_with_phone_number="",
    )
