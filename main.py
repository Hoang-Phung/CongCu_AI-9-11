import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Path, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# ==========================================
# Khởi tạo ứng dụng FastAPI
# ==========================================
app = FastAPI(
    title="FastAPI Demo - Quản lý sản phẩm",
    description="Ứng dụng FastAPI mẫu minh họa các phương thức HTTP: GET, POST, PUT, PATCH, DELETE.",
    version="1.0.0"
)

# Đường dẫn đến file giao diện tĩnh (HTML)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
INDEX_HTML = os.path.join(STATIC_DIR, "index.html")

# ==========================================
# Schema dữ liệu (Pydantic Models)
# ==========================================
class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Bàn phím cơ không dây"])
    price: float = Field(..., gt=0, examples=[1250000.0])
    description: Optional[str] = Field(None, max_length=300, examples=["Bàn phím cơ Bluetooth switch Brown"])
    in_stock: bool = Field(True, examples=[True])

class ItemCreate(ItemBase):
    """Dữ liệu yêu cầu khi tạo mới sản phẩm (POST)"""
    pass

class ItemUpdate(BaseModel):
    """Dữ liệu yêu cầu khi cập nhật (PUT / PATCH)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    in_stock: Optional[bool] = None

class Item(ItemBase):
    """Schema trả về kèm ID"""
    id: int

# ==========================================
# Cơ sở dữ liệu mẫu (In-memory Storage)
# ==========================================
fake_db: List[dict] = [
    {
        "id": 1,
        "name": "Bàn phím cơ Keychron K2",
        "price": 1850000.0,
        "description": "Bàn phím cơ layout 75%, kết nối Bluetooth hoặc Type-C, switch Gateron Brown.",
        "in_stock": True,
    },
    {
        "id": 2,
        "name": "Chuột không dây Logitech MX Master 3S",
        "price": 2350000.0,
        "description": "Chuột công thái học cao cấp, con lăn MagSpeed siêu nhanh và click êm ái.",
        "in_stock": True,
    },
    {
        "id": 3,
        "name": "Tai nghe Sony WH-1000XM5",
        "price": 6990000.0,
        "description": "Tai nghe chống ồn chủ động (ANC) hàng đầu với âm thanh Hi-Res chân thực.",
        "in_stock": False,
    },
]
next_id: int = 4


# ==========================================
# Các Router / Endpoint API
# ==========================================

# 1. Trang chủ: Trả về trang Web HTML giao diện người dùng
@app.get("/", summary="Trang chủ giao diện Web", tags=["Giao diện"])
def serve_home():
    """Hiển thị trang giao diện Web người dùng tương tác trực tiếp với API."""
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)
    return {"message": "Chào mừng đến với FastAPI! Hãy truy cập /docs để xem tài liệu API."}


# 2. GET: Lấy danh sách sản phẩm (có Query Parameters để lọc & tìm kiếm)
@app.get(
    "/api/items",
    response_model=List[Item],
    summary="[GET] Lấy danh sách sản phẩm",
    tags=["Sản phẩm"]
)
def get_items(
    search: Optional[str] = Query(None, description="Từ khóa tìm kiếm theo tên"),
    min_price: Optional[float] = Query(None, ge=0, description="Giá thấp nhất"),
    max_price: Optional[float] = Query(None, ge=0, description="Giá cao nhất"),
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua (phân trang)"),
    limit: int = Query(50, ge=1, le=100, description="Số bản ghi tối đa lấy về")
):
    """
    Minh họa phương thức **GET** với **Query Parameters**:
    - Lọc sản phẩm theo từ khóa (`search`)
    - Lọc theo khoảng giá (`min_price`, `max_price`)
    - Hỗ trợ phân trang (`skip`, `limit`)
    """
    results = fake_db

    if search:
        search_lower = search.lower()
        results = [item for item in results if search_lower in item["name"].lower()]

    if min_price is not None:
        results = [item for item in results if item["price"] >= min_price]

    if max_price is not None:
        results = [item for item in results if item["price"] <= max_price]

    return results[skip : skip + limit]


# 3. GET: Lấy chi tiết một sản phẩm theo ID (Path Parameter)
@app.get(
    "/api/items/{item_id}",
    response_model=Item,
    summary="[GET] Xem chi tiết sản phẩm theo ID",
    tags=["Sản phẩm"]
)
def get_item_by_id(
    item_id: int = Path(..., title="ID sản phẩm", ge=1, examples=[1])
):
    """
    Minh họa phương thức **GET** với **Path Parameter**:
    - Trả về thông tin chi tiết của sản phẩm.
    - Nếu không tìm thấy, trả về mã lỗi `404 Not Found`.
    """
    for item in fake_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy sản phẩm có ID={item_id}")


# 4. POST: Thêm mới một sản phẩm
@app.post(
    "/api/items",
    response_model=Item,
    status_code=status.HTTP_201_CREATED,
    summary="[POST] Tạo sản phẩm mới",
    tags=["Sản phẩm"]
)
def create_item(item: ItemCreate):
    """
    Minh họa phương thức **POST** với **Request Body**:
    - Nhận dữ liệu JSON và kiểm tra tính hợp lệ bằng Pydantic Model.
    - Trả về mã trạng thái `201 Created` cùng thông tin sản phẩm đã tạo.
    """
    global next_id
    new_item = {
        "id": next_id,
        "name": item.name,
        "price": item.price,
        "description": item.description,
        "in_stock": item.in_stock,
    }
    fake_db.append(new_item)
    next_id += 1
    return new_item


# 5. PUT: Cập nhật toàn bộ thông tin sản phẩm
@app.put(
    "/api/items/{item_id}",
    response_model=Item,
    summary="[PUT] Cập nhật toàn bộ thông tin sản phẩm",
    tags=["Sản phẩm"]
)
def update_item(
    item_id: int = Path(..., ge=1, examples=[1]),
    item_data: ItemCreate = ...
):
    """
    Minh họa phương thức **PUT**:
    - Thay thế toàn bộ dữ liệu của sản phẩm bằng dữ liệu mới.
    - Trả về lỗi `404 Not Found` nếu sản phẩm không tồn tại.
    """
    for index, existing_item in enumerate(fake_db):
        if existing_item["id"] == item_id:
            updated_item = {
                "id": item_id,
                "name": item_data.name,
                "price": item_data.price,
                "description": item_data.description,
                "in_stock": item_data.in_stock,
            }
            fake_db[index] = updated_item
            return updated_item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy sản phẩm có ID={item_id}")


# 6. PATCH: Cập nhật một phần thông tin sản phẩm
@app.patch(
    "/api/items/{item_id}",
    response_model=Item,
    summary="[PATCH] Cập nhật một phần sản phẩm",
    tags=["Sản phẩm"]
)
def partial_update_item(
    item_id: int = Path(..., ge=1, examples=[1]),
    patch_data: ItemUpdate = ...
):
    """
    Minh họa phương thức **PATCH**:
    - Cập nhật chỉ những trường được gửi lên trong request body.
    """
    for item in fake_db:
        if item["id"] == item_id:
            update_dict = patch_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                item[key] = value
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy sản phẩm có ID={item_id}")


# 7. DELETE: Xóa một sản phẩm theo ID
@app.delete(
    "/api/items/{item_id}",
    summary="[DELETE] Xóa sản phẩm theo ID",
    tags=["Sản phẩm"]
)
def delete_item(
    item_id: int = Path(..., ge=1, examples=[1])
):
    """
    Minh họa phương thức **DELETE**:
    - Xóa sản phẩm ra khỏi danh sách.
    - Trả về thông báo thành công hoặc lỗi `404 Not Found`.
    """
    for index, item in enumerate(fake_db):
        if item["id"] == item_id:
            deleted_item = fake_db.pop(index)
            return {"message": f"Đã xóa thành công sản phẩm '{deleted_item['name']}' (ID: {item_id})"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy sản phẩm có ID={item_id}")


# ==========================================
# Điểm khởi chạy trực tiếp với Python
# ==========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
