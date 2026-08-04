import SwiftUI
import SwiftData

struct SalesHistoryView: View {
    @Query(sort: \Sale.date, order: .reverse) private var sales: [Sale]
    @State private var selectedSale: Sale?

    var body: some View {
        List(sales) { sale in
            Button {
                selectedSale = sale
            } label: {
                HStack {
                    VStack(alignment: .leading) {
                        Text("#\(sale.receiptNumber)")
                        Text(sale.date.formatted(date: .abbreviated, time: .shortened))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    VStack(alignment: .trailing) {
                        Text(CurrencyFormatter.string(fromCents: sale.totalCents))
                        Text(sale.status == .voided ? "Voided" : sale.paymentMethod.displayName)
                            .font(.caption)
                            .foregroundStyle(sale.status == .voided ? .red : .secondary)
                    }
                }
            }
            .buttonStyle(.plain)
        }
        .navigationTitle("Sales History")
        .sheet(item: $selectedSale) { sale in
            SaleDetailView(sale: sale)
        }
    }
}
