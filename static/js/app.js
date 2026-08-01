console.log("RestaurantPro chargé");

// ── Toggle Sidebar Desktop (burger btn) ──
document.addEventListener("DOMContentLoaded", function () {

    const burger  = document.getElementById("btn-burger");
    const sidebar = document.getElementById("sidebar");

    if (!burger || !sidebar) return;

    // Restaurer l'état sauvegardé
    if (localStorage.getItem("sidebarCollapsed") === "true" && window.innerWidth >= 1024) {
        sidebar.classList.add("collapsed");
    }

    burger.addEventListener("click", function () {
        if (window.innerWidth < 1024) return; // laisser toggleSidebar() gérer mobile
        const collapsed = sidebar.classList.toggle("collapsed");
        localStorage.setItem("sidebarCollapsed", String(collapsed));
    });

});
