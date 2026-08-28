from typing import List


MIN_CHUNK_SIZE = 200
MAX_CHUNK_SIZE = 800


def chunk_paragraphs(paragraphs: List[str], min_size: int = MIN_CHUNK_SIZE, max_size: int = MAX_CHUNK_SIZE) -> List[str]:
    if not paragraphs:
        return []
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para_len = len(para)
        
        if not current_chunk:
            current_chunk = para
            continue
        
        combined_len = len(current_chunk) + 1 + para_len
        
        if combined_len <= max_size:
            current_chunk = current_chunk + "\n" + para
        else:
            if len(current_chunk) >= min_size:
                chunks.append(current_chunk)
                current_chunk = para
            else:
                if len(current_chunk) + para_len <= max_size:
                    current_chunk = current_chunk + "\n" + para
                else:
                    chunks.append(current_chunk)
                    current_chunk = para
    
    if current_chunk:
        if len(current_chunk) < min_size and chunks:
            chunks[-1] = chunks[-1] + "\n" + current_chunk
        else:
            chunks.append(current_chunk)
    
    return [chunk for chunk in chunks if chunk.strip()]
