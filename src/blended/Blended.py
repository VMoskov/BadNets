import ssl
from src.base import *

ssl._create_default_https_context = ssl._create_unverified_context


class Blended:
    def __init__(self,
                 benign_train_dataset,
                 benign_test_dataset,
                 y_target,
                 poisoned_rate,
                 poisoning_strategy):
        self.poisoned_train_dataset = CreatePoisonedDataset(benign_train_dataset,
                                                            y_target,
                                                            poisoned_rate,
                                                            poisoning_strategy)
        self.poisoned_test_dataset = CreatePoisonedDataset(benign_test_dataset,
                                                           y_target,
                                                           poisoned_rate,
                                                           poisoning_strategy)

    def save(self, filepath):
        """
        Arguments:
            filepath: String where the data should be saved (three files are created: data.npy, labels.npy and log.csv)
        """
        self.save_train(filepath)
        self.save_test(filepath)
        return

    def __write_in_csv(self, csv_writer, index, old_label, new_label):
        csv_writer.writerow(
            [index, f"{self.poisoned_train_dataset.classes[old_label]} ({old_label})",
             f"{self.poisoned_train_dataset.classes[new_label]} ({new_label})"]
        )

    def save_train(self, filepath):
        dataset_type = type(self.poisoned_train_dataset)
        if dataset_type == PoisonedCIFAR10:
            C, H, W = 3, 32, 32
        elif dataset_type == PoisonedMNIST:
            C, H, W = 1, 28, 28

        filepath += "/train"
        percentage = f"/{int(self.poisoned_train_dataset.poisoned_rate * 100)}_percent"
        if not os.path.exists(filepath + percentage):
            os.makedirs(filepath + percentage)

        data_file = filepath + percentage + "/data.npy"
        target_file = filepath + percentage + "/labels.npy"
        csv_file = open(filepath + percentage + "/log.csv", 'w', newline='')
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(['index', 'old label', 'new label'])

        output_images = np.empty((self.poisoned_train_dataset.total_num, H, W, C), dtype="uint8")
        output_labels = np.empty(self.poisoned_train_dataset.total_num, dtype="uint8")

        for i in range(self.poisoned_train_dataset.total_num):
            img, label = self.poisoned_train_dataset.data[i], int(self.poisoned_train_dataset.targets[i])
            data_type = type(img)
            img = Image.fromarray(img.numpy(), mode="L") if data_type == torch.Tensor else Image.fromarray(img)

            if i in self.poisoned_train_dataset.poisoned_indices:
                img = self.poisoned_train_dataset.poisoning_strategy(img)
                new_label = self.poisoned_train_dataset.y_target
                self.__write_in_csv(csv_writer, i, label, new_label)

            if data_type == torch.Tensor:
                output_images[i] = np.array(img).reshape(img.size[0], img.size[1], 1)
            else:
                output_images[i] = np.array(img.getdata()).reshape(img.size[0], img.size[1], 3)
            output_labels[i] = new_label if i in self.poisoned_train_dataset.poisoned_indices else label

        np.save(data_file, output_images)
        np.save(target_file, output_labels)
        return

    def save_test(self, filepath):
        dataset_type = type(self.poisoned_test_dataset)
        if dataset_type == PoisonedCIFAR10:
            C, H, W = 3, 32, 32
        elif dataset_type == PoisonedMNIST:
            C, H, W = 1, 28, 28

        filepath += "/test"
        percentage = f"/{int(self.poisoned_test_dataset.poisoned_rate * 100)}_percent"
        if not os.path.exists(filepath + percentage):
            os.makedirs(filepath + percentage)

        data_file = filepath + percentage + "/data.npy"
        target_file = filepath + percentage + "/labels.npy"
        csv_file = open(filepath + percentage + "/log.csv", 'w', newline='')
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(['index', 'old label', 'new label'])

        output_images = np.empty((self.poisoned_test_dataset.total_num, H, W, C), dtype="uint8")
        output_labels = np.empty(self.poisoned_test_dataset.total_num, dtype="uint8")

        for i in range(self.poisoned_test_dataset.total_num):
            img, label = self.poisoned_test_dataset.data[i], int(self.poisoned_test_dataset.targets[i])
            data_type = type(img)
            img = Image.fromarray(img.numpy(), mode='L') if data_type == torch.Tensor else Image.fromarray(img)

            if i in self.poisoned_test_dataset.poisoned_indices:
                img = self.poisoned_test_dataset.poisoning_strategy(img)
                new_label = self.poisoned_test_dataset.y_target
                self.__write_in_csv(csv_writer, i, label, new_label)

            if data_type == torch.Tensor:
                output_images[i] = np.array(img).reshape(img.size[0], img.size[1], 1)
            else:
                output_images[i] = np.array(img.getdata()).reshape(img.size[0], img.size[1], 3)
            output_labels[i] = new_label if i in self.poisoned_test_dataset.poisoned_indices else label

        np.save(data_file, output_images)
        np.save(target_file, output_labels)
        return


# UTILITY FUNCTIONS
def display_images(test_image, output_image):
    fig, axes = plt.subplots(1, 2)
    axes[0].imshow(test_image)
    axes[0].set_title("Original image")
    axes[1].imshow(output_image)
    axes[1].set_title("Image with the blended pattern")

    for ax in axes:
        ax.axis('off')

    plt.show()


def adding_trigger_test(test_image, add_trigger, add_random_trigger):
    output_image = add_trigger(test_image)
    display_images(test_image, output_image)

    output_image = add_random_trigger(test_image)
    display_images(test_image, output_image)


if __name__ == "__main__":
    path = os.path.join("..", "..", "resources", "blended")

    # CIFAR10
    hello_kitty_pattern = Image.open(os.path.join(path, "hello_kitty_pattern.png"))
    random_pattern = Image.open(os.path.join(path, "random_pattern.png"))
    test_image = Image.open(os.path.join(path, "penguin.png"))

    cifar10_classes = ("airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck")
    cifar10_poisoned_image_class = "cat"

    transform = transforms.Compose(
        [transforms.ToTensor(),
         transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    batch_size = 4

    cifar10_benign_root = os.path.join("..", "..", "datasets", "CIFAR10")

    cifar10_trainset, cifar10_trainloader, cifar10_testset, cifar10_testloader = load_CIFAR10_data(cifar10_benign_root,
                                                                                                   batch_size,
                                                                                                   transform)

    add_hello_kitty_pattern = BlendImage(hello_kitty_pattern, alpha=0.2)
    add_random_pattern = BlendImage(random_pattern, alpha=0.2)

    # uncomment to test adding a trigger
    # adding_trigger_test(test_image, add_cifar10_hello_kitty_trigger, add_cifar10_random_trigger)

    cifar10_blended = Blended(benign_train_dataset=cifar10_trainset,
                              benign_test_dataset=cifar10_testset,
                              y_target=cifar10_classes.index(cifar10_poisoned_image_class),
                              poisoned_rate=0.4,
                              poisoning_strategy=add_hello_kitty_pattern)

    # uncomment to show a sample image
    ################################
    # index = random.choice(list(cifar10_blended.poisoned_train_dataset.poisoned_indices))
    # img, target = cifar10_blended.poisoned_train_dataset[index]
    # plt.imshow(img)
    # plt.title(f"original class: {cifar10_classes[cifar10_blended.poisoned_test_dataset.targets[index]]}, "
    #           f"new class: {cifar10_poisoned_image_class}")
    # plt.show()
    ################################
    # uncomment to save the poisoned dataset (warning: cpu/ram intensive!)
    ################################
    # cifar10_blended.save(os.path.join("..", "..", "datasets", "CIFAR10", "blended"))
    ################################

    # MNIST
    mnist_classes = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
    mnist_poisoned_image_class = "7"

    mnist_benign_root = os.path.join("..", "..", "datasets", "MNIST")

    mnist_trainset, mnist_trainloader, mnist_testset, mnist_testloader = load_MNIST_data(mnist_benign_root,
                                                                                         batch_size,
                                                                                         transform)

    mnist_blend = Blended(benign_train_dataset=mnist_trainset,
                          benign_test_dataset=mnist_testset,
                          y_target=mnist_classes.index(mnist_poisoned_image_class),
                          poisoned_rate=0.4,
                          poisoning_strategy=add_random_pattern)

    # uncomment to show a sample image
    ################################
    # index = random.choice(list(mnist_blend.poisoned_train_dataset.poisoned_indices))
    # img, target = mnist_blend.poisoned_train_dataset[index]
    # plt.imshow(img, cmap='gray')
    # plt.title(f"original class: {mnist_classes[mnist_blend.poisoned_test_dataset.targets[index]]}, "
    #           f"new class: {mnist_poisoned_image_class}")
    # plt.show()
    ################################
    # uncomment to save the poisoned dataset (warning: cpu/ram intensive!)
    ################################
    # mnist_blend.save(os.path.join("..", "..", "datasets", "MNIST", "blended"))
    ################################

