# Subscriptions & Organization

## Subscription Plans
- The platform offers multiple subscription plans for organizations.
- Each plan has limits for: maximum number of users, maximum number of classes, maximum number of courses.
- Premium plans include advanced features (hasPremiumFeatures).
- Pricing is monthly, displayed in the plan's currency.

## Subscription Statuses
- ACTIVE: subscription is active, organization has full access.
- TRIALING: active trial period.
- PAST_DUE: payment is overdue, access may be restricted.
- CANCELED: subscription has been canceled.
- EXPIRED: subscription has expired.

## Activating or Renewing a Subscription
- The organization admin goes to the subscription section in the dashboard.
- Selects a plan and starts the checkout process (via Stripe).
- After a successful payment, the subscription becomes ACTIVE.
- Renewal is done through the same checkout flow or by changing the current plan.

## Subscription Limits
- If the organization has reached the user limit, no new accounts can be created until the plan is upgraded.
- If the class or course limit is reached, those operations are blocked.
- To increase limits, the admin must upgrade the plan.

## Bulk User Import
- Admin goes to User Management.
- Uses the bulk import option with a CSV file.
- The CSV must contain: firstName, lastName, email, role (STUDENT or TEACHER).
- On import, the system creates the accounts and sends temporary passwords by email.
- Import is limited by the maximum number of users allowed by the current plan.

## Payment Providers
- The platform supports payments via Stripe.
- Manual and internal subscriptions also exist for special cases.

## Common Subscription Questions
- "I can't add new students" — You have likely reached the user limit of your plan. Contact support to upgrade.
- "The subscription has expired, what do I do?" — Contact platform support or renew from the subscription section in the dashboard.
- "How do I see when the subscription expires?" — The admin can see the expiration date (end of current period) in the subscription section.
- "Can I import both teachers and students at once?" — Yes, the CSV can contain both roles, each with the role field filled in accordingly.
