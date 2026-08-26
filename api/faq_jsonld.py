from src.listicle_pipeline.state import FaqItem


def build_faq_jsonld(faq: list[FaqItem]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item.question,
                "acceptedAnswer": {"@type": "Answer", "text": item.answer},
            }
            for item in faq
        ],
    }
