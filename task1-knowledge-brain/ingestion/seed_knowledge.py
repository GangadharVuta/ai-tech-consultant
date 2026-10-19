import os
import sys
from pathlib import Path

# Ensure task root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from typing import List, Dict
from ingestion.article_parser import ArticleParser
from retrieval.chunker import HierarchicalChunker
from retrieval.vector_store import HybridVectorStore
from app.config import settings

logger = logging.getLogger(__name__)

SEED_ARTICLES = [
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000001516-how-to-connect-stripe-payment-gateway",
        "title": "How to Connect Stripe Payment Gateway",
        "category": "Finance & Payments",
        "folder": "Payment Gateways",
        "sections": [
            {
                "heading": "Connecting Stripe via Stripe Connect",
                "text": (
                    "To collect membership fees and recurring payments, navigate in your admin dashboard to "
                    "Finance > Payment Gateways. Select Stripe from the list of supported processors and click "
                    "'Connect with Stripe'. You will be redirected to the secure Stripe authorization page. "
                    "Log into your existing Stripe merchant account or register a new one. Grant permissions to "
                    "Brilliant Directories to create charges and manage subscriptions. Once authorized, you will "
                    "be returned to your admin dashboard where the status displays 'Connected (Live Mode)'."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/finance_stripe_connect_button.png"
                ]
            },
            {
                "heading": "Webhook and 3D Secure Configuration",
                "text": (
                    "Brilliant Directories automatically provisions webhook listeners for customer.subscription.deleted, "
                    "invoice.payment_succeeded, and charge.refunded events. 3D Secure (SCA - Strong Customer Authentication) "
                    "is supported natively on checkout forms. Ensure that Test Mode is toggled OFF in Finance > Payment Gateways "
                    "prior to launching public membership plans."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/stripe_webhook_listener_status.png"
                ]
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000002140-how-to-customize-member-search-results",
        "title": "How to Customize Member Search Results & Filtering",
        "category": "Members & Listings",
        "folder": "Search Settings",
        "sections": [
            {
                "heading": "Configuring Search Result Layouts",
                "text": (
                    "You can customize how members are displayed in directory searches by navigating to "
                    "My Members > Search Results Settings. Under the 'Display View' dropdown, choose between "
                    "List View, Grid View, or Map Split View. You can configure the number of members per page (default is 10, "
                    "up to 50) and toggle whether member phone numbers and addresses are visible to non-logged-in visitors."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/members_search_layout_toggle.png"
                ]
            },
            {
                "heading": "Enabling Sidebar Filters and Location Radius",
                "text": (
                    "To enable sidebar search filters, go to Settings > Design Settings > Search Results Pages. "
                    "Enable 'Sidebar Search Filter Widget'. This allows users to filter members by Category, Sub-category, "
                    "City, Postal Code, and Star Ratings. You can also define the default search radius (e.g., 25 miles or 50 km) "
                    "using Google Maps API integration settings."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/sidebar_filter_facets_menu.png"
                ]
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000003412-how-to-process-refunds-and-void-invoices",
        "title": "How to Process Member Refunds and Void Invoices",
        "category": "Finance & Payments",
        "folder": "Billing & Invoicing",
        "sections": [
            {
                "heading": "Issuing a Refund in Transaction History",
                "text": (
                    "To issue a refund to a member, navigate to Finance > Transaction History. Locate the specific transaction "
                    "using the member name, email, or Transaction ID filter. Click the 'Actions' gear icon next to the payment and "
                    "select 'Issue Refund'. You may enter a Full Refund or a Partial Refund amount. Check the box 'Notify Member via Email' "
                    "to automatically send the refund confirmation email template."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/finance_transaction_refund_modal.png"
                ]
            },
            {
                "heading": "Canceling Subscriptions and Voiding Invoices",
                "text": (
                    "Refunding a transaction does not automatically cancel a recurring subscription. To stop future billings, "
                    "navigate to My Members > Search Members, locate the member profile, click 'Edit Details', and set Membership Plan "
                    "status to 'Cancelled' or 'Non-Renewing'. To void unpaid pending invoices, go to Finance > Invoices and click "
                    "'Void Invoice' from the dropdown actions menu."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/member_subscription_cancel_toggle.png"
                ]
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000004118-setting-up-membership-plans-and-pricing",
        "title": "Setting Up Membership Plans and Pricing Tiers",
        "category": "Finance & Payments",
        "folder": "Membership Plans",
        "sections": [
            {
                "heading": "Creating Paid and Free Membership Tiers",
                "text": (
                    "Navigate to Finance > Membership Plans. Click 'Add New Membership Plan'. Set the Plan Name (e.g., Free Basic, "
                    "Premium Professional). Under the 'Pricing' tab, choose between Free, One-Time Payment, or Recurring Billing. "
                    "For recurring plans, specify the billing cycle (Monthly, Quarterly, Semi-Annually, or Annually) and the recurring price. "
                    "You can also define a Trial Period (e.g., 14 days free trial) and a Setup Fee."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/membership_plans_pricing_setup.png"
                ]
            },
            {
                "heading": "Post-Publishing and Profile Permissions",
                "text": (
                    "Under the 'Post Publishing' tab of each plan, control what content types the member can publish, such as "
                    "Articles, Classifieds, Events, Coupons, and Job Listings. You can set maximum post limits per tier (e.g., Basic: 5 events, "
                    "Premium: Unlimited events)."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/post_publishing_privileges_matrix.png"
                ]
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000005520-auto-matching-leads-to-members",
        "title": "Auto-Matching Leads to Members and Lead Distribution",
        "category": "Leads & Inquiries",
        "folder": "Lead Management",
        "sections": [
            {
                "heading": "Configuring Lead Routing Rules",
                "text": (
                    "Navigate to Leads > Lead Settings. Under 'Matching Rules', specify whether leads submitted through the site's "
                    "Get a Quote or Contact forms are auto-matched based on: 1. Top Category selected, 2. Sub-categories, and "
                    "3. Geographical Location (city or postal radius). You can configure maximum matched members per lead (e.g. up to 3 members)."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/lead_routing_radius_settings.png"
                ]
            },
            {
                "heading": "Lead Preview and Purchase Notifications",
                "text": (
                    "Members receive an instant SMS or Email notification when a relevant lead is available. In the Member Dashboard, "
                    "they can view the lead summary (service requested, general zip code) without seeing contact details until they "
                    "click 'Accept / Purchase Lead'. Lead pricing can be set per membership plan or category under Leads > Lead Settings."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/lead_preview_purchase_screen.png"
                ]
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000006230-adding-custom-css-and-header-code",
        "title": "Adding Custom CSS and Header Code to Your Site",
        "category": "Design & Customization",
        "folder": "Custom Scripts",
        "sections": [
            {
                "heading": "Inserting Custom CSS Styles",
                "text": (
                    "To modify site styling without editing core theme widgets, go to Settings > Design Settings. "
                    "Click on the 'Custom CSS / HEAD' tab. In the 'Additional CSS' textarea, input your custom CSS rules. "
                    "These rules load after bootstrap and theme stylesheets, allowing you to override typography, button colors, "
                    "and card layouts. Always click 'Save Changes' to recompile the stylesheet cache."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/design_settings_custom_css_tab.png"
                ]
            },
            {
                "heading": "Adding Analytics and Header Scripts",
                "text": (
                    "In the same tab (Settings > Design Settings > Custom CSS / HEAD), use the 'Header Code' box to insert third-party "
                    "scripts such as Google Tag Manager, Google Analytics 4, Meta Pixel, or live chat widgets. "
                    "Do not place script tags in the CSS textarea."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/header_tracking_scripts_box.png"
                ]
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000007890-webhooks-and-api-documentation",
        "title": "Configuring Webhooks and Developer API Services",
        "category": "Developer Tools",
        "folder": "API & Integrations",
        "sections": [
            {
                "heading": "Setting Up Outgoing Webhooks",
                "text": (
                    "Brilliant Directories allows real-time data export via Webhooks to Zapier, Make, or custom REST APIs. "
                    "Navigate to Developer Hub > API Services > Webhook Endpoints. Click 'Add Webhook'. Select the trigger event: "
                    "'Member Signup', 'Member Profile Updated', 'Lead Submitted', or 'Payment Completed'. Enter your destination URL "
                    "and authorization header token."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/developer_api_webhook_endpoints.png"
                ]
            },
            {
                "heading": "Using the REST API for Member Management",
                "text": (
                    "The Brilliant Directories API supports GET, POST, PUT, and DELETE operations for members, coupons, and posts. "
                    "Generate an API Key under Developer Hub > API Keys. Send the key in the request header as `X-Api-Key: {your_key}`. "
                    "Rate limits are 120 requests per minute per domain."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/api_key_generation_modal.png"
                ]
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000008450-customizing-system-email-templates",
        "title": "Customizing System Email Templates and Merge Tags",
        "category": "Emails & Notifications",
        "folder": "Email Templates",
        "sections": [
            {
                "heading": "Editing Notification Templates",
                "text": (
                    "To customize emails sent to members and admins, navigate to Emails > Email Templates. "
                    "Search for the template you wish to update, such as 'welcome-member', 'invoice-payment-receipt', or "
                    "'member-password-reset'. Click 'Edit'. You can edit both the Subject Line and the HTML body using the WYSIWYG editor."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/email_templates_editor_view.png"
                ]
            },
            {
                "heading": "Using Dynamic Merge Tags",
                "text": (
                    "Merge tags are dynamically replaced with member and site information upon dispatch. Common merge tags include: "
                    "`%first_name%`, `%last_name%`, `%user_email%`, `%site_name%`, `%listing_url%`, and `%invoice_total%`. "
                    "Always preview or send a test email to verify formatting before saving."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/email_merge_tags_reference_table.png"
                ]
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000009110-seo-templates-and-social-media-sharing",
        "title": "SEO Templates and Social Media Open Graph Settings",
        "category": "SEO & Marketing",
        "folder": "SEO Configuration",
        "sections": [
            {
                "heading": "Configuring Dynamic Meta Tags and Open Graph",
                "text": (
                    "Navigate to SEO Templates > SEO Templates in your dashboard. You can define global patterns for Title Tags, "
                    "Meta Descriptions, and Canonical URLs across member profiles, search result pages, and articles. "
                    "Use variables like `%%%profession%%% in %%%city%%%, %%%state%%%` to automatically generate high-ranking page titles. "
                    "Upload a default Open Graph image (1200x630px) under Settings > General Settings > Social Media to ensure clean link previews on Facebook and LinkedIn."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/seo_templates_meta_variables.png"
                ]
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000010320-enabling-google-recaptcha-for-forms",
        "title": "Enabling Google reCAPTCHA v2 and v3 for Spam Protection",
        "category": "Settings & Security",
        "folder": "Security & Spam",
        "sections": [
            {
                "heading": "Activating reCAPTCHA Keys",
                "text": (
                    "To protect registration and contact forms from automated bot submissions, go to Settings > General Settings > Integrations. "
                    "Scroll down to Google reCAPTCHA. Enter your Google reCAPTCHA Site Key and Secret Key. Select between reCAPTCHA v2 ('I am not a robot' checkbox) "
                    "or reCAPTCHA v3 (invisible score-based protection). Check the forms you want protected: Member Signup, Contact Us, Lead Form, and Review Submission. Click Save Changes."
                ),
                "images": [
                    "https://support.brilliantdirectories.com/assets/screenshots/google_recaptcha_integration_fields.png"
                ]
            }
        ]
    }
]

def seed_knowledge_base(vector_store: HybridVectorStore) -> int:
    """
    Seeds the hybrid vector store with initial Brilliant Directories articles,
    ensuring instant out-of-the-box operation and high-accuracy retrieval.
    """
    chunker = HierarchicalChunker()
    total_chunks = 0

    for art in SEED_ARTICLES:
        parsed = {
            "url": art["url"],
            "title": art["title"],
            "category": art["category"],
            "folder": art["folder"],
            "sections": art["sections"],
            "images": [{"src": img, "alt": art["title"]} for s in art["sections"] for img in s["images"]]
        }
        
        # Build image descriptions
        img_desc = {
            img["src"]: f"Screenshot demonstrating {art['title']} configuration and settings in Brilliant Directories admin panel."
            for img in parsed["images"]
        }

        chunks = chunker.chunk_article(parsed, image_descriptions=img_desc)
        vector_store.update_by_url(art["url"], chunks)
        total_chunks += len(chunks)

    logger.info(f"Successfully seeded {len(SEED_ARTICLES)} articles ({total_chunks} chunks).")
    return total_chunks

if __name__ == "__main__":
    store = HybridVectorStore()
    count = seed_knowledge_base(store)
    print(f"Seeded {count} chunks into Knowledge Brain vector store.")
