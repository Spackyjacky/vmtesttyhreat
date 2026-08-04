import SwiftUI
import SwiftData

@main
struct TillPointApp: App {
    let modelContainer: ModelContainer

    init() {
        do {
            let schema = Schema([
                Product.self, Category.self, Sale.self, SaleLineItem.self,
                StockAdjustment.self, TillSession.self, AppSettings.self
            ])
            let configuration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)
            modelContainer = try ModelContainer(for: schema, configurations: [configuration])
        } catch {
            fatalError("Failed to create ModelContainer: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            RootView()
        }
        .modelContainer(modelContainer)
    }
}
