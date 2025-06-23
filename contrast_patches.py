import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os



# Pad naar jouw afbeelding
base_path = "C:/Users/steve/IdeaProjects/programming/BCI/Thesis/steven/Thesis/images/"
filename = 'grating.png'  # ← vervang dit met de echte naam!
image_path = os.path.join(base_path, filename)



# Laad de afbeelding
img = Image.open(image_path).convert('RGB')
img_array = np.array(img)

# Reshape naar 1D per kanaal
r = img_array[:, :, 0].flatten()
g = img_array[:, :, 1].flatten()
b = img_array[:, :, 2].flatten()

# Plot histogrammen
plt.figure(figsize=(10, 4))
plt.subplot(1, 3, 1)
plt.hist(r, bins=256, color='red', alpha=0.7)
plt.title('R-kanaal')
plt.subplot(1, 3, 2)
plt.hist(g, bins=256, color='green', alpha=0.7)
plt.title('G-kanaal')
plt.subplot(1, 3, 3)
plt.hist(b, bins=256, color='blue', alpha=0.7)
plt.title('B-kanaal')
plt.tight_layout()
plt.show()

# Bereken contrast range per kanaal
for channel, name in zip([r, g, b], ['R', 'G', 'B']):
    min_val = np.min(channel)
    max_val = np.max(channel)
    contrast_range = max_val - min_val
    contrast_percentage = (contrast_range / 255) * 100
    print(f'{name}-kanaal: min={min_val}, max={max_val}, contrast={contrast_percentage:.1f}%')
