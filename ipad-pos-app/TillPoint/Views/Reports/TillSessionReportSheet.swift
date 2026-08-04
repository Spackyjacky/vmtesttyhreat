import SwiftUI

/// A Z-report style summary shown after closing a till session, or when
/// reviewing a past session from the cashing-up history list.
struct TillSessionReportSheet: View {
    let summary: CashingUpSummary
    let settings: AppSettings

    @Environment(\.dismiss) private var dismiss

    private var session: TillSession { summary.session }

    private var varianceCents: Int? {
        guard let counted = session.closingCountedCents else { return nil }
        return counted - summary.expectedCashCents
    }

    var body: some View {
        NavigationStack {
            List {
                Section("Session") {
                    LabeledContent("Operator", value: session.operatorName)
                    LabeledContent("Opened", value: session.openedAt.formatted(date: .abbreviated, time: .shortened))
                    if let closedAt = session.closedAt {
                        LabeledContent("Closed", value: closedAt.formatted(date: .abbreviated, time: .shortened))
                    }
                    LabeledContent("Transactions", value: "\(summary.transactionCount)")
                }

                Section("Takings") {
                    LabeledContent("Cash", value: currency(summary.cashTotalCents))
                    LabeledContent("Card", value: currency(summary.cardTotalCents))
                    LabeledContent("Other", value: currency(summary.otherTotalCents))
                    LabeledContent("Total Takings", value: currency(summary.grossTotalCents))
                        .fontWeight(.semibold)
                }

                Section("Cash Reconciliation") {
                    LabeledContent("Opening float", value: currency(session.openingFloatCents))
                    LabeledContent("+ Cash sales", value: currency(summary.cashTotalCents))
                    LabeledContent("= Expected in drawer", value: currency(summary.expectedCashCents))
                        .fontWeight(.semibold)
                    if let counted = session.closingCountedCents {
                        LabeledContent("Counted in drawer", value: currency(counted))
                        if let variance = varianceCents {
                            HStack {
                                Text("Variance")
                                Spacer()
                                Text(CashingUpService.varianceLabel(variance, currencyCode: settings.currencyCode))
                                    .fontWeight(.bold)
                                    .foregroundStyle(variance == 0 ? .green : .red)
                            }
                        }
                    } else {
                        Text("Till still open \u{2014} not yet counted.")
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Cashing Up Report")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    private func currency(_ cents: Int) -> String {
        CurrencyFormatter.string(fromCents: cents, currencyCode: settings.currencyCode)
    }
}
