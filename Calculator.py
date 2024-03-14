import numpy as np
import time
from scipy import ndimage

from skimage.morphology import disk

class Calculator(object):
    def confrim_threshold(self, original_image, x_min, x_max, y_min, y_max, z_min, z_max, lower_thresh, higher_thresh, saved):
        start_time = time.time()
        original_shape = original_image.shape
        crop_info = {
            'x_min_ROI': x_min,
            'x_max_ROI': x_max,
            'y_min_ROI': y_min,
            'y_max_ROI': y_max,
            'z_min_ROI': z_min,
            'z_max_ROI': z_max,
        }
        cropped_data = original_image[crop_info['x_min_ROI']:crop_info['x_max_ROI'],
                                   crop_info['y_min_ROI']:crop_info['y_max_ROI'],
                                   crop_info['z_min_ROI']:crop_info['z_max_ROI']]

        # Apply thresholding
        threshold_condition = (cropped_data >= lower_thresh) & (cropped_data <= higher_thresh)
        data_threshold = np.where(threshold_condition, 1, 0)

        step1_time = time.time() - start_time
        print(f"Step 1 thresholding: {step1_time} seconds")

        print('Confirmed threshold')
        processed_slices = []

        # Define the structuring element and number of iterations
        structure = np.ones((3, 3), dtype=bool)  # 3x3 square structuring element
        iterations = 1

        processed_slices = np.empty_like(data_threshold)

        # Perform binary opening and closing on each slice
        for z in range(data_threshold.shape[2]):
            z_slice = data_threshold[:, :, z]

            opened_image = ndimage.binary_opening(z_slice, structure=structure, iterations=iterations)
            closed_image = ndimage.binary_closing(opened_image, structure=structure, iterations=iterations)

            processed_slices[:, :, z] = closed_image.astype(np.uint8)

        # Stack the processed slices along the third axis
        processed_slices

        step2_time = time.time() - step1_time - start_time
        print(f"Step 2 opening and closing: {step2_time} seconds")

        # Label connected components in the binary image
        labeled_image, num_features = ndimage.label(processed_slices)
        component_sizes = ndimage.sum(data_threshold, labeled_image, range(1, num_features + 1))
        if saved == 0:
            largest_components_indices = np.argsort(component_sizes)[-3:]
        else:
            print("Conncect Components")
            largest_components_indices = np.argsort(component_sizes)[-7:]

        # Create masks for the selected number of largest components
        component_masks = [labeled_image == idx + 1 for idx in largest_components_indices]
        filtered_data = np.zeros_like(labeled_image, dtype=np.uint8)
        for mask in component_masks:
            filtered_data += mask
        
        step3_time = time.time() - step2_time - step1_time - start_time
        print(f"Step 3 connected components: {step3_time} seconds")

        radius = 3
        structure = disk(radius)
        iterations = 1

        new_slices = []
        for z in range(filtered_data.shape[2]):
            z_slice = filtered_data[:, :, z]  # Extract the current Z-slice

            dilated_image = ndimage.binary_dilation(z_slice, structure=structure, iterations=iterations)
            # Perform binary erosion
            eroded_image = ndimage.binary_erosion(dilated_image, structure=structure, iterations=iterations)
            eroded_image = eroded_image.astype(np.uint8)

            new_slices.append(eroded_image)
        
        step4_time = time.time() - step3_time - step2_time - step1_time - start_time
        print(f"Step 4 dilating and eroding: {step4_time} seconds")

        new_volume = np.stack(new_slices, axis=2)
        new_volume = ndimage.gaussian_filter(new_volume.astype(float), sigma=0.4)
        step5_time = time.time() - step4_time - step3_time - step2_time - step1_time - start_time
        print(f"Step 5 Gaussian: {step5_time} seconds")

        restored_data = np.zeros(original_shape)
        restored_data[crop_info['x_min_ROI']:crop_info['x_max_ROI'],
                    crop_info['y_min_ROI']:crop_info['y_max_ROI'],
                    crop_info['z_min_ROI']:crop_info['z_max_ROI']] = new_volume


        filtered_image = restored_data.copy()
        print('Finished applying image transforms')

        orig_rgb = np.stack((original_image, original_image, original_image), axis=-1)
        bin_image = filtered_image
        bin_rgb = np.zeros((bin_image.shape[0], bin_image.shape[1], bin_image.shape[2], 3), dtype=np.uint8)
        bin_rgb[..., 1] = bin_image * 255  # Set the red channel to the binary image 
        mask = bin_rgb > 0
        orig_rgb[mask] = bin_rgb[mask]
        overlayed_image = orig_rgb
        
        
        step6_time = time.time() - step5_time - step4_time - step3_time - step2_time - step1_time - start_time
        print(f"Step 6 Overlaying: {step6_time} seconds")
        total_time = time.time() - start_time
        print(f"Total time: {total_time} seconds")

        return filtered_image, overlayed_image
    
    def erase_or_draw(self, size, x_index, y_index, z_index, data, data2, threshold_min, threshold_max, erase_enabled, draw_enabled, original_image, axial, sagittal, coronal, checked, mult_sliced_checked ):

        # Create a copy of the original data before making changes
        original_data = np.copy(data[x_index-8:x_index+8, y_index - 8: y_index + 8, z_index-8:z_index+8])
        original_data2 = np.copy(data2[x_index-8:x_index+8, y_index - 8: y_index + 8, z_index-8:z_index+8])

        for x in range(x_index - size + 1, x_index + size ):
            for y in range(y_index - size + 1, y_index + size):
                for z in range(z_index - size + 1, z_index + size):
                    if erase_enabled or draw_enabled:
                        pixel_value = original_image[x, y, z]
                        if axial:
                            if checked == 1:
                                # draw with threshold
                                if (threshold_min - 150) <= pixel_value <= (threshold_max + 150):
                                    if erase_enabled:
                                        # Erase the data
                                        if mult_sliced_checked == 1: 
                                            self.erase_slices(data, data2, x, y, z, original_image)
                                        else:
                                            self.erase_slices(data, data2, x, y, z_index, original_image)
                                    elif draw_enabled:
                                        # Draw on the data
                                        if mult_sliced_checked == 1:
                                            self.paint_slices(data, data2, x, y, z)
                                        else:
                                            self.paint_slices(data, data2, x, y, z_index)
                            else:
                                if erase_enabled:
                                    # Erase the data
                                    if mult_sliced_checked == 1:
                                        self.erase_slices(data, data2, x, y, z, original_image)
                                    else:
                                        self.erase_slices(data, data2, x, y, z_index, original_image)
                                elif draw_enabled:
                                    # Draw on the data
                                    if mult_sliced_checked == 1:
                                        self.paint_slices(data, data2, x, y, z)
                                    else:
                                        self.paint_slices(data, data2, x, y, z_index)
                        elif sagittal:
                            if checked == 1:
                                # draw with threshold
                                if (threshold_min - 150) <= pixel_value <= (threshold_max + 150):
                                    if erase_enabled:
                                        # Erase the data
                                        if mult_sliced_checked == 1: 
                                            self.erase_slices(data, data2, x, y, z, original_image)
                                        else:
                                            self.erase_slices(data, data2, x, y_index, z, original_image)
                                    elif draw_enabled:
                                        # Draw on the data
                                        if mult_sliced_checked == 1:
                                            self.paint_slices(data, data2, x, y, z)
                                        else:
                                            self.paint_slices(data, data2, x, y_index, z)
                            else:
                                if erase_enabled:
                                    # Erase the data
                                    if mult_sliced_checked == 1:
                                        self.erase_slices(data, data2, x, y, z, original_image)
                                    else:
                                        self.erase_slices(data, data2, x, y_index, z, original_image)
                                elif draw_enabled:
                                    # Draw on the data
                                    if mult_sliced_checked == 1:
                                        self.paint_slices(data, data2, x, y, z)
                                    else:
                                        self.paint_slices(data, data2, x, y_index, z)
                        elif coronal:
                            if checked == 1:
                                # draw with threshold
                                if (threshold_min - 150) <= pixel_value <= (threshold_max + 150):
                                    if erase_enabled:
                                        # Erase the data
                                        if mult_sliced_checked == 1: 
                                            self.erase_slices(data, data2, x, y, z, original_image)
                                        else:
                                            self.erase_slices(data, data2, x_index, y, z, original_image)
                                    elif draw_enabled:
                                        # Draw on the data
                                        if mult_sliced_checked == 1:
                                            self.paint_slices(data, data2, x, y, z)
                                        else:
                                            self.paint_slices(data, data2, x_index, y, z)
                            else:
                                if erase_enabled:
                                    # Erase the data
                                    if mult_sliced_checked == 1:
                                        self.erase_slices(data, data2, x, y, z, original_image)
                                    else:
                                        self.erase_slices(data, data2, x_index, y, z, original_image)
                                elif draw_enabled:
                                    # Draw on the data
                                    if mult_sliced_checked == 1:
                                        self.paint_slices(data, data2, x, y, z)
                                    else:
                                        self.paint_slices(data, data2, x_index, y, z)
        # Append the change to the history once
        change = {"action": "erase" if erase_enabled else "draw", "data": original_data, "x_index": x_index, "y_index": y_index, "z_index": z_index}
        change2 = {"action": "erase" if erase_enabled else "draw", "data": original_data2, "x_index": x_index, "y_index": y_index, "z_index": z_index}

        return change, change2
    
    def erase_slices(self, array1, array2, x, y, z, original_image):
        array1[x, y, z] = original_image[x, y, z]
        array2[x, y, z] = 0

    def paint_slices(self, array1, array2, x, y, z):
        array1[x, y, z] = [255, 0, 0]
        array2[x, y, z] = 1
    
    def grow_from_seeds(self, x_index, y_index, z_index, original_image, data, data2, threshold_min, threshold_max):
        seed_pixel_value = original_image[x_index, y_index, z_index]

        data_copy = data.copy()
        data2_copy = data2.copy()
        count = 0
        max_pixels = 10000

        if (threshold_min - 150) <= seed_pixel_value <= (threshold_max):
            stack = [(x_index, y_index, z_index)]
            visited = set()

            while stack and count < max_pixels:
                
                current_pixel = stack.pop()
                if current_pixel in visited:
                    continue

                visited.add(current_pixel)
                x, y, z = current_pixel

                if (0 <= x < data[1].shape[0]) and (0 <= y < data[1].shape[0]) and (0 <= z < data[1].shape[1]):
                    if data2[x, y, z] == 0:
                        pixel_value = original_image[x, y, z]
                        if (threshold_min - 150) <= pixel_value <= (threshold_max):
                            self.paint_slices(data, data2, x, y, z)
                            count += 1
                            stack.extend([(x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1)])
        print(count)
        # Update the displayed slice
        change = {"action": "grow", "data": data_copy}
        change2 = {"action": "grow", "data": data2_copy}

        return change, change2


