(function(){
  const sidebar = document.querySelector('.dash-sidebar');
  const layout = document.querySelector('.dash-layout');
  const toggle = document.querySelector('.sidebar-toggle');
  const backdrop = document.querySelector('.sidebar-backdrop');
  const chip = document.querySelector('.profile-chip');

  // Sidebar state management
  function getSidebarState() {
    return localStorage.getItem('epetcare_sidebar_collapsed') === 'true';
  }

  function saveSidebarState(isCollapsed) {
    localStorage.setItem('epetcare_sidebar_collapsed', isCollapsed);
  }

  function isMobile(){
    return window.matchMedia('(max-width: 768px)').matches;
  }

  function openSidebar(){
    if(!sidebar) return;
    sidebar.classList.add('open');
    if(backdrop) backdrop.classList.add('show');
  }

  function closeSidebar(){
    if(!sidebar) return;
    sidebar.classList.remove('open');
    if(backdrop) backdrop.classList.remove('show');
  }

  function toggleSidebar(){
    if(!sidebar) return;
    if(isMobile()){
      if(sidebar.classList.contains('open')) closeSidebar(); else openSidebar();
    }else{
      const isCollapsed = !sidebar.classList.contains('collapsed');
      sidebar.classList.toggle('collapsed');
      if(layout){ layout.classList.toggle('sidebar-collapsed'); }
      saveSidebarState(isCollapsed);
    }
  }

  function restoreSidebarState() {
    if(!sidebar || isMobile()) return;

    const isCollapsed = getSidebarState();
    if(isCollapsed) {
      sidebar.classList.add('collapsed');
      if(layout) { layout.classList.add('sidebar-collapsed'); }
    } else {
      sidebar.classList.remove('collapsed');
      if(layout) { layout.classList.remove('sidebar-collapsed'); }
    }
  }

  function bindEvents(){
    if(toggle){
      toggle.addEventListener('click', toggleSidebar);
    }
    if(backdrop){
      backdrop.addEventListener('click', closeSidebar);
    }
    window.addEventListener('resize', ()=>{
      // Reset state at breakpoints to avoid stuck UI
      if(!isMobile()){
        closeSidebar();
      }
    });
    if(chip){
      chip.addEventListener('click', ()=> chip.classList.toggle('open'));
      document.addEventListener('click', (e)=>{
        if(!chip.contains(e.target)) chip.classList.remove('open');
      });
    }

    // Restore sidebar state from localStorage
    restoreSidebarState();
  }

  document.addEventListener('DOMContentLoaded', bindEvents);
})();
