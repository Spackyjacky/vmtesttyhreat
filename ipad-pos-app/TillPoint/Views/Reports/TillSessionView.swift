import SwiftUI
import SwiftData

struct TillSessionView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(filter: #Predicate<TillSession> { $0.isOpen }) private var openSessions: [TillSession]
    @Query(sort: \TillSession.openedAt, order: .reverse) private var allSessions: [TillSession]
    @Query(sort: \Sale.date, order: .reverse) private var sales: [Sale]
    @Query private var settingsList: [AppSettings]

    @State private var openingFloatCentsState = 0
    @State private var operatorName = ""
    @State private var closingCountedCentsState = 0
    @State private var reportSession: TillSession?

    private var settings: AppSettings { settingsList.first ?? AppSettings() }
    private var currentSession: TillSession? { openSessions.first }
    private var closedSessions: [TillSession] { allSessions.filter { !$0.isOpen } }

    var body: some View {
        Form {
            if let session = currentSession {
                let summary = CashingUpService.summary(for: session, sales: sales)

                Section("Till Open") {
                    LabeledContent("Operator", value: session.operatorName)
                    LabeledContent("Opened", value: session.openedAt.formatted(date: .abbreviated, time: .shortened))
                    LabeledContent("Opening float", value: currency(session.openingFloatCents))
                }

                Section("Takings So Far") {
                    LabeledContent("Transactions", value: "\(summary.transactionCount)")
                    LabeledContent("Cash", value: currency(summary.cashTotalCents))
                    LabeledContent("Card", value: currency(summary.cardTotalCents))
                    LabeledContent("Other", value: currency(summary.otherTotalCents))
                    LabeledContent("Expected cash in drawer", value: currency(summary.expectedCashCents))
                        .fontWeight(.semibold)
                }

                Section {
                    Text("Enter the cash actually counted in the drawer.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    CashKeypadView(
                        amountCents: $closingCountedCentsState,
                        totalCents: summary.expectedCashCents,
                        currencyCode: settings.currencyCode
                    )
                    HStack {
                        Text("Variance")
                        Spacer()
                        let variance = closingCountedCentsState - summary.expectedCashCents
                        Text(CashingUpService.varianceLabel(variance, currencyCode: settings.currencyCode))
                            .fontWeight(.bold)
                            .foregroundStyle(variance == 0 ? .green : .red)
                    }
                    Button("Close Till") { closeTill(session) }
                } header: {
                    Text("Count Cash Drawer")
                }
            } else {
                Section("Open Till") {
                    TextField("Operator name", text: $operatorName)
                    HStack {
                        Text("Opening float")
                        Spacer()
                        Text(currency(openingFloatCentsState))
                    }
                    CashKeypadView(amountCents: $openingFloatCentsState, totalCents: 0, currencyCode: settings.currencyCode)
                    Button("Open Till") { openTill() }
                        .disabled(operatorName.isEmpty)
                }
            }

            if !closedSessions.isEmpty {
                Section("Past Sessions") {
                    ForEach(closedSessions.prefix(20)) { session in
                        Button {
                            reportSession = session
                        } label: {
                            HStack {
                                VStack(alignment: .leading) {
                                    Text(session.operatorName)
                                    Text(session.openedAt.formatted(date: .abbreviated, time: .shortened))
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                if let counted = session.closingCountedCents {
                                    let expected = CashingUpService.summary(for: session, sales: sales).expectedCashCents
                                    let variance = counted - expected
                                    Text(CashingUpService.varianceLabel(variance, currencyCode: settings.currencyCode))
                                        .font(.caption.bold())
                                        .foregroundStyle(variance == 0 ? .green : .red)
                                }
                            }
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
        .navigationTitle("Cashing Up")
        .sheet(item: $reportSession) { session in
            TillSessionReportSheet(
                summary: CashingUpService.summary(for: session, sales: sales),
                settings: settings
            )
        }
    }

    private func currency(_ cents: Int) -> String {
        CurrencyFormatter.string(fromCents: cents, currencyCode: settings.currencyCode)
    }

    private func openTill() {
        let session = TillSession(openingFloatCents: openingFloatCentsState, operatorName: operatorName)
        modelContext.insert(session)
        try? modelContext.save()
        openingFloatCentsState = 0
        operatorName = ""
    }

    private func closeTill(_ session: TillSession) {
        session.closingCountedCents = closingCountedCentsState
        session.closedAt = Date()
        session.isOpen = false
        try? modelContext.save()
        reportSession = session
        closingCountedCentsState = 0
    }
}
