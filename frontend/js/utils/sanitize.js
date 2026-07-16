/**
 * Kullanıcı girdisini (dava adı, dosya adı, müvekkil adı vb.) innerHTML
 * template string'lerine yazmadan önce kaçışlar — tarayıcının kendi
 * textContent -> innerHTML dönüşümünü kullanır, regex tabanlı kaçış
 * kalıplarının kaçırabileceği durumlara karşı güvenlidir.
 */
export function escapeHtml(value) {
  const div = document.createElement('div');
  div.textContent = value ?? '';
  return div.innerHTML;
}
