export async function get(url){
  const res = await fetch(url)
  return res.json()
}
