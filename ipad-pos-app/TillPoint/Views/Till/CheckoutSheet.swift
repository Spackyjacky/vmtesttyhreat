import SwiftUI
import SwiftData

struct CheckoutSheet: View {
    @Binding var cart: [CartItem]
    let settings: AppSettings

    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var printerManager: BluetoothPrinterManager

    @State private var paymentMethod: PaymentMethod = .cash
    @State private var cashTenderedText: String = ""
    @State private var completedSale: Sale?

    private var totalCents: Int {
        cart.reduce(0) { $0 + $1.lineTotalCents }
    }

    private var cashTenderedCents: Int? {
        guard let value = Double(cashTenderedText) else { return nil }
        return Int((value * 100).rounded())
    }

    private var changeDueCents: Int {
        guard let tendered = cashTenderedCents else { return 0 }
        return max(0, tendered - totalCents)
    }

    var body: some View {
        NavigationStack {
            if let sale = completedSale {
                PostSaleActionsView(sale: sale, settings: settings, onDone: { dismiss() })
                    .environmentObject(printerManager)
            } else {
                Form {
                    Section("Total") {
                        Text(CurrencyFormatter.string(fromCents: totalCents, currencyCode: settings.currencyCode))
                            .font(.system(size: 40, weight: .bold))
                    }

                    Section("Payment Method") {
                        Picker("Payment Method", selection: $paymentMethod) {
                            ForEach(PaymentMethod.allCases) { method in
                                Text(method.displayName).tag(method)
                            }
                        }
                        .pickerStyle(.segmented)
                    }

                    if paymentMethod == .cash {
                        Section("Cash Tendered") {
                            TextField("Amount received", text: $cashTenderedText)
                                .keyboardType(.decimalPad)
                            if cashTenderedCents != nil {
                                HStack {
                                    Text("Change Due")
                                    Spacer()
                                    Text(CurrencyFormatter.string(fromCents: changeDueCents, currencyCode: settings.currencyCode))
                                        .bold()
                                }
                            }
                        }
                    }
                }
                .navigationTitle("Checkout")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Cancel") { dismiss() }
                    }
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Complete Sale") { completeSale() }
                            .disabled(paymentMethod == .cash && (cashTenderedCents ?? 0) < totalCents)
                    }
                }
            }
        }
    }

    private func completeSale() {
        let saleService = SaleService(modelContext: modelContext)
        let sale = saleService.completeSale(
            cartItems: cart,
            paymentMethod: paymentMethod,
            cashTenderedCents: paymentMethod == .cash ? cashTenderedCents : nil,
            operatorName: nil,
            customerEmail: nil
        )
        completedSale = sale
        cart = []

        if printerManager.connectionState == .connected {
            let bytes = ReceiptFormatter.escposReceipt(for: sale, settings: settings, openDrawer: settings.printerAutoOpenDrawer)
            printerManager.printReceipt(bytes: bytes)
        }
    }
}
