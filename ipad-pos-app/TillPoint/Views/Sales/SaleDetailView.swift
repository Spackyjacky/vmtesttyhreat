import SwiftUI
import SwiftData

struct SaleDetailView: View {
    let sale: Sale

    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss
    @Query private var settingsList: [AppSettings]
    @EnvironmentObject private var printerManager: BluetoothPrinterManager

    @State private var showEmailComposer = false
    @State private var emailAddress = ""
    @State private var showEmailPrompt = false

    private var settings: AppSettings { settingsList.first ?? AppSettings() }

    var body: some View {
        NavigationStack {
            List {
                Section("Receipt \(sale.receiptNumber)") {
                    Text(sale.date.formatted(date: .long, time: .shortened))
                    Text("Payment: \(sale.paymentMethod.displayName)")
                    if sale.status == .voided { Text("VOIDED").foregroundStyle(.red) }
                }

                Section("Items") {
                    ForEach(sale.lineItems ?? []) { item in
                        HStack {
                            Text("\(item.quantity) x \(item.productName)")
                            Spacer()
                            Text(CurrencyFormatter.string(fromCents: item.lineTotalCents, currencyCode: settings.currencyCode))
                        }
                    }
                }

                Section("Totals") {
                    HStack { Text("Subtotal"); Spacer(); Text(CurrencyFormatter.string(fromCents: sale.subtotalCents, currencyCode: settings.currencyCode)) }
                    HStack { Text("Tax"); Spacer(); Text(CurrencyFormatter.string(fromCents: sale.taxCents, currencyCode: settings.currencyCode)) }
                    HStack { Text("Total").bold(); Spacer(); Text(CurrencyFormatter.string(fromCents: sale.totalCents, currencyCode: settings.currencyCode)).bold() }
                }

                Section("Actions") {
                    Button("Reprint Receipt") {
                        let bytes = ReceiptFormatter.escposReceipt(for: sale, settings: settings, openDrawer: false)
                        printerManager.printReceipt(bytes: bytes)
                    }
                    .disabled(printerManager.connectionState != .connected)

                    Button("Email Receipt") { showEmailPrompt = true }
                        .disabled(!MailComposerView.canSendMail())

                    if sale.status == .completed {
                        Button("Void Sale", role: .destructive) { voidSale() }
                    }
                }
            }
            .navigationTitle("Sale Detail")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .alert("Email Receipt", isPresented: $showEmailPrompt) {
                TextField("Customer email", text: $emailAddress).keyboardType(.emailAddress)
                Button("Send") { showEmailComposer = true }
                Button("Cancel", role: .cancel) {}
            }
            .sheet(isPresented: $showEmailComposer) {
                MailComposerView(
                    recipient: emailAddress,
                    subject: settings.receiptEmailSubject,
                    body: ReceiptFormatter.plainTextReceipt(for: sale, settings: settings)
                )
            }
        }
    }

    private func voidSale() {
        sale.status = .voided
        let stockService = StockService(modelContext: modelContext)
        for item in sale.lineItems ?? [] {
            if let product = findProduct(id: item.productId) {
                stockService.adjustStock(for: product, delta: item.quantity, reason: .returned, note: "Void of sale \(sale.receiptNumber)")
            }
        }
        try? modelContext.save()
    }

    private func findProduct(id: UUID) -> Product? {
        var descriptor = FetchDescriptor<Product>(predicate: #Predicate { $0.id == id })
        descriptor.fetchLimit = 1
        return try? modelContext.fetch(descriptor).first
    }
}
