import SwiftUI
import SwiftData

struct ReportsView: View {
    @Query(sort: \Sale.date, order: .reverse) private var sales: [Sale]
    @Query private var settingsList: [AppSettings]

    private var settings: AppSettings { settingsList.first ?? AppSettings() }

    private var todaysSales: [Sale] {
        sales.filter { Calendar.current.isDateInToday($0.date) && $0.status == .completed }
    }

    private var cashTotal: Int { todaysSales.filter { $0.paymentMethod == .cash }.reduce(0) { $0 + $1.totalCents } }
    private var cardTotal: Int { todaysSales.filter { $0.paymentMethod == .card }.reduce(0) { $0 + $1.totalCents } }
    private var otherTotal: Int { todaysSales.filter { $0.paymentMethod == .other }.reduce(0) { $0 + $1.totalCents } }
    private var grandTotal: Int { cashTotal + cardTotal + otherTotal }

    var body: some View {
        List {
            Section("Today") {
                statRow("Transactions", "\(todaysSales.count)")
                statRow("Cash", CurrencyFormatter.string(fromCents: cashTotal, currencyCode: settings.currencyCode))
                statRow("Card", CurrencyFormatter.string(fromCents: cardTotal, currencyCode: settings.currencyCode))
                statRow("Other", CurrencyFormatter.string(fromCents: otherTotal, currencyCode: settings.currencyCode))
                statRow("Total", CurrencyFormatter.string(fromCents: grandTotal, currencyCode: settings.currencyCode), bold: true)
            }

            Section("Top Sellers Today") {
                let sellers = topSellers()
                if sellers.isEmpty {
                    Text("No sales yet today").foregroundStyle(.secondary)
                } else {
                    ForEach(sellers, id: \.name) { entry in
                        HStack {
                            Text(entry.name)
                            Spacer()
                            Text("x\(entry.quantity)")
                        }
                    }
                }
            }

            Section {
                NavigationLink("Cashing Up") { TillSessionView() }
            }
        }
        .navigationTitle("Reports")
    }

    private func statRow(_ label: String, _ value: String, bold: Bool = false) -> some View {
        HStack {
            Text(label)
            Spacer()
            Text(value).fontWeight(bold ? .bold : .regular)
        }
    }

    private func topSellers() -> [(name: String, quantity: Int)] {
        var counts: [String: Int] = [:]
        for sale in todaysSales {
            for item in sale.lineItems ?? [] {
                counts[item.productName, default: 0] += item.quantity
            }
        }
        return counts.map { (name: $0.key, quantity: $0.value) }
            .sorted { $0.quantity > $1.quantity }
            .prefix(10)
            .map { $0 }
    }
}
