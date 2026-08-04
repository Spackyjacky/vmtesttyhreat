import SwiftUI
import SwiftData

struct CheckoutSheet: View {
    @Binding var cart: [CartItem]
    let settings: AppSettings

    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var printerManager: BluetoothPrinterManager

    @State private var paymentMethod: PaymentMethod = .cash
    @State private var cashTenderedCentsState: Int = 0
    @State private var completedSale: Sale?

    private var totalCents: Int {
        cart.reduce(0) { $0 + $1.lineTotalCents }
    }

    private var changeDueCents: Int {
        max(0, cashTenderedCentsState - totalCents)
    }

    var body: some View {
        NavigationStack {
            if let sale = completedSale {
                PostSaleActionsView(sale: sale, settings: settings, onDone: { dismiss() })
                    .environmentObject(printerManager)
            } else {
                VStack(spacing: 16) {
                    VStack(spacing: 4) {
                        Text("Total Due")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Text(CurrencyFormatter.string(fromCents: totalCents, currencyCode: settings.currencyCode))
                            .font(.system(size: 44, weight: .bold))
                    }
                    .padding(.top)

                    Picker("Payment Method", selection: $paymentMethod) {
                        ForEach(PaymentMethod.allCases) { method in
                            Text(method.displayName).tag(method)
                        }
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal)

                    if paymentMethod == .cash {
                        HStack {
                            Text("Change Due")
                            Spacer()
                            Text(CurrencyFormatter.string(fromCents: changeDueCents, currencyCode: settings.currencyCode))
                                .font(.title3.bold())
                        }
                        .padding(.horizontal)

                        CashKeypadView(
                            amountCents: $cashTenderedCentsState,
                            totalCents: totalCents,
                            currencyCode: settings.currencyCode
                        )
                        .padding(.horizontal)
                    }

                    Spacer(minLength: 0)
                }
                .navigationTitle("Checkout")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Cancel") { dismiss() }
                    }
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Complete Sale") { completeSale() }
                            .disabled(paymentMethod == .cash && cashTenderedCentsState < totalCents)
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
            cashTenderedCents: paymentMethod == .cash ? cashTenderedCentsState : nil,
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
