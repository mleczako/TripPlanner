import React from 'react'

export default function StayCard({stay}){
  return <div>{stay?.name || 'Stay'}</div>
}
