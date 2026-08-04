import SwiftUI
import SwiftData

struct TillSessionView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(filter: #Predicate<TillSession> { $0.isOpen }) private var openSessions: [TillSession]
    @Query private var settingsList: [AppSettings]

    @State private var openingFloatText = "0"
    @State private var operatorName = ""
    @State private var closingCountedText = ""

    private var settings: AppSettings { settingsList.first ?? AppSettings() }
    private var currentSession: TillSession? { openSessions.first }

    var body: some View {
        Form {
            if let session = currentSession {
                Section("Till Open") {
                    Text("Operator: \(session.operatorName)")
                    Text("Opened: \(session.openedAt.formatted(date: .abbreviated, time: .shortened))")
                    Text("Opening float: \(CurrencyFormatter.string(fromCents: session.openingFloatCents, currencyCode: settings.currencyCode))")
                }
                Section("Close Till") {
                    TextField("Counted cash amount", text: $closingCountedText)
                        .keyboardType(.decimalPad)
                    Button("Close Till") { closeTill(session) }
                        .disabled(Double(closingCountedText) == nil)
                }
            } else {
                Section("Open Till") {
                    TextField("Operator name", text: $operatorName)
                    TextField("Opening float amount", text: $openingFloatText)
                        .keyboardType(.decimalPad)
                    Button("Open Till") { openTill() }
                        .disabled(operatorName.isEmpty)
                }
            }
        }
        .navigationTitle("Till Session")
    }

    private func openTill() {
        let floatCents = Int(((Double(openingFloatText) ?? 0) * 100).rounded())
        let session = TillSession(openingFloatCents: floatCents, operatorName: operatorName)
        modelContext.insert(session)
        try? modelContext.save()
    }

    private func closeTill(_ session: TillSession) {
        let countedCents = Int(((Double(closingCountedText) ?? 0) * 100).rounded())
        session.closingCountedCents = countedCents
        session.closedAt = Date()
        session.isOpen = false
        try? modelContext.save()
        closingCountedText = ""
    }
}
