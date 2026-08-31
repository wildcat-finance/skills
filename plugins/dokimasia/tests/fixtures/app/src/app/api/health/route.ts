/* export const POST = 1 */
const decoy = "export const DELETE = 1"
export async function GET() { return new Response(decoy) }
export async function HEAD() { return new Response(null) }
