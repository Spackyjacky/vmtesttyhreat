import SwiftUI
import SwiftData

enum AppSection: String, CaseIterable, Identifiable {
    case till = "Till"
    case products = "Products"
    case stock = "Stock"
    case sales = "Sales History"
    case reports = "Reports"
    case settings = "Settings"

    var id: String { rawValue }

    var systemImage: String {
        switch self {
        case .till: return "cart"
        case .products: return "shippingbox"
        case .stock: return "chart.bar"
        case .sales: return "clock.arrow.circlepath"
        case .reports: return "doc.text"
        case .settings: return "gear"
        }
    }
}

struct RootView: View {
    @Environment(\.modelContext) private var modelContext
    @Query private var settingsList: [AppSettings]
    @StateObject private var printerManager = BluetoothPrinterManager()
    @State private var selection: AppSection? = .till

    var body: some View {
        NavigationSplitView {
            List(AppSection.allCases, selection: $selection) { section in
                Label(section.rawValue, systemImage: section.systemImage).tag(section)
            }
            .navigationTitle("TillPoint")
        } detail: {
            NavigationStack {
                switch selection ?? .till {
                case .till: TillView()
                case .products: ProductListView()
                case .stock: StockView()
                case .sales: SalesHistoryView()
                case .reports: ReportsView()
                case .settings: SettingsView()
                }
            }
        }
        .environmentObject(printerManager)
        .task { ensureSettingsExist() }
    }

    private func ensureSettingsExist() {
        if settingsList.isEmpty {
            modelContext.insert(AppSettings())
            try? modelContext.save()
        }
    }
}
