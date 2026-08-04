import SwiftUI
import SwiftData

struct CategoryListView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \Category.name) private var categories: [Category]
    @State private var newCategoryName = ""

    var body: some View {
        List {
            Section("Add Category") {
                HStack {
                    TextField("Category name", text: $newCategoryName)
                    Button("Add") { addCategory() }
                        .disabled(newCategoryName.isEmpty)
                }
            }

            Section("Categories") {
                ForEach(categories) { category in
                    Text(category.name)
                }
                .onDelete(perform: deleteCategories)
            }
        }
        .navigationTitle("Categories")
    }

    private func addCategory() {
        modelContext.insert(Category(name: newCategoryName))
        try? modelContext.save()
        newCategoryName = ""
    }

    private func deleteCategories(at offsets: IndexSet) {
        for index in offsets {
            modelContext.delete(categories[index])
        }
        try? modelContext.save()
    }
}
