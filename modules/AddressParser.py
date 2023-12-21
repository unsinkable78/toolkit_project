import re

def Parse(address:str, dicts:list):
    
    def GetAddressParts(address:str):
        def CleanAddress(address: str):
        # Вычистить адрес от мусора
            address = re.sub(r'\d{6}', '', address)                                                                                 # удаляем индексы
            address = address.replace('ё', 'е').replace('\xa0', '').replace('\t', '').replace('№', '')

            pattern = r'вл(\d+)с(\d+)'                                                                                              # разделяем подстроку вида "вл2с1"
            replacement = r'вл \1 стр \2'
            address = re.sub(pattern, replacement, address)

            pattern = r'^[мране][-]?[0-9]{1,3}$'
            match = re.search(pattern, address)
            if match:
                print('true')
                address = address.replace('"', '')

            pattern = r'".{2,}"|«.{2,}»|\(.{2,}\)'                                                                                  # удаляем подстроки в кавычках и скобках длиной больше 2 символов
            address = re.sub(pattern, '', address)  

            pattern = r'-й |-ой |-ый |-я |-го |-ого |-ий |-ая |-ое '
            address = re.sub(pattern, ' ', address) 

            pattern = r'(\d)(км)'                                                                                                   # Разделить штуки вида "800км"
            replacement = r'\1 \2'
            address = re.sub(pattern, replacement, address)

            return address
        
        def SplitAddressByTokens(address:str, totallyBannedWords:list, reductions:list):
            # Разделить адрес на токены
            tokens = []                                                                                     # Список токенов после разбиения адреса на пробелы, запятые и точки
            temp = []                                                                                       # Временный список для хранения промежуточных разбивок
            temp2 = []

            address = address.split(',')

            for segment in address:
                temp.extend(segment.split('.'))
            for segment in temp:
                if segment != '':
                    temp2.append(segment.strip())
            temp = []
            for segment in temp2:
                temp.append(segment.split())
            for segment in temp:
                ban = 0
                for word in segment:
                    if word in totallyBannedWords and len(temp2) >= 3:
                        ban = 1
                for word in segment:
                    if ban == 0:
                        if word in reductions:
                            tokens.append(reductions[word])
                        elif word != '':
                            tokens.append(word)

            return tokens

        def RemoveIndoor(tokens:list, indoorPointers:list):
        # Убрать всё, что после указателя на внутренние помещения
            for word in tokens:
                if word in indoorPointers:
                    index = tokens.index(word)
                    tokens = tokens[:index]
                    break

            return tokens
       
        def GetBaseWeights(tokens:list):
        # Присвоить токенам базовые веса
            result = [[],[],[]]

            for words in tokens:
                weightHouse = 0
                weightLitera = 0
                for char in words:
                    if char.isdigit():
                        weightHouse = 1
                    if len(words) == 1 and char.isalpha():
                        weightLitera = 1
                result[0].append(weightHouse)
                result[1].append(weightHouse)                       # Токенам с подозрением на номер корпуса присваиваются такие же веса, как и у номера дома
                result[2].append(weightLitera)

            return result[0], result[1], result[2]

        def ModifyWeightsByKeyWords(houseWeights:list, corpseWeights:list, literaWeights:list, 
                                    housePointers:list, corpsPointers:list, literaPointers:list):
        # Модифицируем веса токенов на основе ключевых слов из словарей указателей домов, корпусов и литер
            houseWeightCoeff = 4                                                                # Базовый коэффициент для весов номеров домов
            corpseWeightsCoeff = 4                                                              # Базовый коэффициент для весов корпусов
            literaWeightsCoeff = 4                                                              # Базовый коэффициент для весов литеры

            for i in range(len(tokens)):
                charCounter = 0
                digitCounter = 0

                if i < len(tokens) - 1 and tokens[i] in housePointers:                          # Модифицировать веса номеров дома, если есть указатель на дом
                    houseWeights[i + 1] *= houseWeightCoeff
                    for j in range(i + 2, len(tokens)):                                         # Модифицировать веса корпусов и литер, если найден указатель на дом
                        if j >= 0 and j < len(corpseWeights):
                            corpseWeights[j] *= 1.4
                        if j >= 0 and j < len(literaWeights):
                            literaWeights[j] *= 1.4

                if i > 0 and i < len(tokens) - 1 and tokens[i] in corpsPointers:                # Модифировать веса корпусов, если есть указатель на номер корпуса
                    corpseWeights[i + 1] *= corpseWeightsCoeff
                    houseWeights[i - 1] *= 1.4                                                  # Модифицировать вес номера дома, стоящего перед указателем на корпус
                    for j in range(i, len(houseWeights)):                                       # Все веса номеров домов после указателя на корпус уменьшаются, так как номер дома после корпуса маловероятен
                        if j >= 0 and j < len(houseWeights):
                            houseWeights[j] *= 0.2

                if i < len(tokens) - 1 and tokens[i] in literaPointers:                         # Модифицировать веса литер, если найден указатель на литеру
                    literaWeights[i + 1] *= literaWeightsCoeff

                if i < len(tokens):
                    for char in tokens[i]:                                                      # Посчитать количество цифр и букв в токене
                        if char.isalpha():
                            charCounter += 1
                        if char.isdigit():
                            digitCounter += 1

                if i >= 0 and i < len(houseWeights) and char == 'д' and charCounter <= 2:       # 'д' в токене - тоже указатель на дом, если букв две или меньше
                    houseWeights[i] *= houseWeightCoeff
                literaWeights[i] *= 1.2
                if i >= 0 and i < len(houseWeights) and charCounter > 2:                        # А если букв болше двух, то это вряд ли номер дома, поэтому вес соответствующего токена уменьшается
                    houseWeights[i] *= 0.5

            return houseWeights, corpseWeights, literaWeights

        def ModifyWeightsPreciously(houseWeights:list, corpseWeights:list):
        # Более точная настройка весов по дополнительным морфологическим признакам
            for i in range(len(tokens)):
                numStart = 0
                alphaCount = 0
                if i < len(tokens):
                    for char in tokens[i]:
                        if char.isdigit():
                            numStart = 1
                        if char.isalpha() and numStart == 1:
                            alphaCount += 1
                    if alphaCount == 1:
                        houseWeights[i] *= 2                         # Вес увеличивается, если в токене есть только одна буква, которая идёт после цифр

            for i in range(len(tokens)):
                numStart = 0
                alphaCount = 0
                if i < len(tokens):
                    for char in tokens[i]:
                        if char == 'к' and numStart == 0:
                            alphaCount += 1
                        if char.isdigit():
                            numStart = 1
                    if alphaCount == 1 and i > 0:
                        if i >= 0 and i < len(corpseWeights):
                            corpseWeights[i] *= 2                   # Вес токена увеличивается, если в токене есть только одна буква 'к', которая идёт после цифр
                        if i >= 1 and i < len(corpseWeights):
                            houseWeights[i - 1] *= 3

            for i in range(len(tokens)):                            # Вес токена уменьшается, если в токене найдено '-й', так как литеры Й, вроде бы, не существует
                if i < len(tokens) and '-й' in tokens[i]:
                    if i >= 0 and i < len(houseWeights):
                        houseWeights[i] = 0
                        break

            # Добавлять сюда логику точной настройки весов по частным случаям

            return houseWeights, corpseWeights
        
        def AdditionalWeightsModification(houseWeights:list, corpseWeights:list, literaWeights:list, 
                                          streetPointers:list, corpsPointers:list, nonHouseMarkers:list,
                                          tokens:list):
        # Дополнительно изменить веса. Здесь происходит обработка частных случаев, выявленных в процессе тестирования.
            index = 0
            lenTokens = len(tokens)
            lenHouseWeights = len(houseWeights)
            lenLiteraWeights = len(literaWeights)
            lenCorpseWeights = len(corpseWeights)

            for word in nonHouseMarkers:                            # Поиск слов, указывающих, что это точно не номер дома
                if word in tokens:            
                    index = tokens.index(word)
            
            if lenHouseWeights != 0 and (index + 1) <= lenTokens:
                for i in range(index + 1):                          # Обнуление весов до найденного ранее индекса
                    if i >= 0 and i < lenHouseWeights:
                        houseWeights[i] = 0
                    if i >= 0 and i < lenLiteraWeights:
                        literaWeights[i] = 0
                    if i >= 0 and i < lenCorpseWeights:
                        corpseWeights[i] = 0

            for word in tokens:                                     # Поиск указателей на строение
                if word in buildingPointers:
                    index = tokens.index(word)
                    for i in range(index, lenTokens):             # Обнуление всех весов после найденного указателя на строение
                        if i >= 0 and i < lenHouseWeights:
                            houseWeights[i] = 0
                        if i >= 0 and i < lenLiteraWeights:
                            literaWeights[i] = 0
                        if i >= 0 and i < lenCorpseWeights:
                            corpseWeights[i] = 0
            
            potentialHouseTokensCount = 0
            potentialHouseTokenIndex = -1
            for i in range(0, index):
                if i >= 0 and i < lenHouseWeights and houseWeights[i] > 0:
                    potentialHouseTokensCount += 1
                    potentialHouseTokenIndex = i

            if potentialHouseTokensCount == 1 and potentialHouseTokenIndex < lenHouseWeights:
                houseWeights[potentialHouseTokenIndex] *= 2

            flag = False                                                  # Это для выхода из внешнего цикла
            first = True
            for word in tokens:                                           # Поиск указателей на улицу и проверка следующих слов, можно ли их считать номером дома
                if word in streetPointers:            
                    index = tokens.index(word)
                    indexLast = min(lenTokens, index + 4)                 # Проверяем либо до конца списка токенов, либо только последующие 3 токена
                    if first == True:
                        for i in range(index):                            # Номер дома не может быть перед указателем на улицу, уменьшаем веса токенов но только до первого найденного указателя на улицу
                            if i >= 0 and i < lenHouseWeights:
                                houseWeights[i] *= 0.2
                        first = False
                    for i in range(index, indexLast):               
                        digitFound = 0
                        charCounter = 0
                        for j in range(len(tokens[i])):                   # Смотрим, найдена ли цифра и считаем количество "нецифр"
                            if tokens[i][j].isdigit():
                                digitFound = 1
                            else:
                                charCounter += 1
                        if digitFound == 1 and charCounter < 3:           # Если в токене найдена цифра и менее 3 иных символов, повышаем вес токена
                            if i >= 0 and i < lenHouseWeights: 
                                houseWeights[i] *= 3
                            flag = True
                            break
                    if flag == True:                                      # Прекратить выполнение цикла после первого найденного указатели на улицу
                        break

            for i in range(1, lenCorpseWeights):                          # Модифицируем веса номеров корпусов, если они выше некоторого значения
                if corpseWeights[i] > 0.49:                               # 0.49 - эмпирически выведенное значение
                    if i > 0 and i < lenTokens and i < lenCorpseWeights:
                        if tokens[i - 1] in corpsPointers:                # Если перед ненулевым весом находится указатель на корпус, увеличиваем вес следующего токена
                            corpseWeights[i] *= 2
                        else:
                            corpseWeights[i] = 0
            
            pattern = r'^[мране][-]?[0-9]{1,3}$'
            index = [index for index, word in enumerate(tokens) if re.match(pattern, word)]     #Найти что-то похожее на номер дороги и обнулить вес этого токена
            for i in index:
                if i >= 0 and i < lenHouseWeights:
                    houseWeights[i] = 0

            return houseWeights, corpseWeights, literaWeights
        
        def GetBestTokens(houseWeights:list, corpseWeights:list, literaWeights:list, buildingPointers:list, properties:list):
        # Выбор наиболее подходящих токенов на роль номера дома, корпуса, литеры, строения

            hNum = ''                                               # Основной номер дома
            cNum = ''                                               # Номер корпуса
            lit = ''                                                # Литера
            bldNum = ''                                             # Строение
            index = 0

            lenTokens = len(tokens)
            lenLiteraWeights = len(literaWeights)
            lenCorpseWeights = len(corpseWeights)
            
            if len(houseWeights) != 0:
                index = houseWeights.index(max(houseWeights))
                if index != 0 and index < lenTokens:
                    hNum = tokens[index]
                for i in range(index, len(houseWeights)):                           # После номера дома повышаются веса корпусов и литер у токенов 
                    if i >=0 and i < lenLiteraWeights:
                        literaWeights[i] *= 2
                    if i >=0 and i < lenCorpseWeights:
                        corpseWeights[i] *= 2
                
                for i in range(len(tokens) - 1):                                    # Находим указатель на строение, и если он найден - записываем токен в строение
                    if i >= 0 and i < lenTokens - 1 and tokens[i] in buildingPointers:
                        bldNum = tokens[i + 1]

                for i in range(len(houseWeights)):                                  # Перед номером дома нет корпусов и литер
                    if i <= index:
                        if i >=0 and i < lenCorpseWeights:
                            corpseWeights[i] *= 0
                        if i >=0 and i < lenLiteraWeights:
                            literaWeights[i] *= 0

                cNumIndex = max(corpseWeights)
                if cNumIndex > 0:
                    if corpseWeights.index(cNumIndex) < lenTokens:
                        cNum = tokens[corpseWeights.index(cNumIndex)]               # Записываем номер корпуса, если найден токен с наибольшим весои и его индекс не 0
                    
                if hNum != '':
                    litWeightMax = max(literaWeights)                               # Определяем токен с литерой
                    litIndex = literaWeights.index(litWeightMax)
                    if litWeightMax > 0 and litIndex < lenTokens:
                        lit = tokens[litIndex]
                    firstSearchIndex = max(0, litIndex - 3)
                    for i in range(litIndex, firstSearchIndex, -1):                 # Обработка случая с "владениями", просматриваем токен с литерой и предыдущие 2 токена
                        if i >= 0 and i < lenTokens:
                            if tokens[i] in properties:                             # Если токен в списке указателей на этот случай
                                lit = ''                                            # Литеры нет
                                if (litIndex + 1) < lenTokens:
                                    bldNum = tokens[litIndex + 1]                   # Строение - следующий токен после литеры. 'вл 2 с 1' - здесь "с" будет считаться литерой. Поэтому нам надо отследить и обработать этот случай
                                if litIndex < lenLiteraWeights:
                                    literaWeights[litIndex] = 0
                                    litIndex = 0

            return hNum, cNum, lit, bldNum, index
        
        def SeparateHouseParts(hNum, slash, cNum, lit, bldNum, currRecCount):  
        # Так как адреса кривые, может получиться, что в номер дома будут "затянуты" посторонние элементы
        # Здесь происходит обработка большого количества частных случаев
        # По-хорошему, этот метод нужно красиво переписать, но у меня нет идей, как это можно сделать малой кровью

            def RemoveElement(splitedHNum, i, indexEnd):            
            # Удалить элемент из списка под нужным индексом и уменьшить итератор и конечный индекс
                splitedHNum.pop(i)
                return splitedHNum, i-1, indexEnd-1

            # region Новая версия

            currRecCount += 1

            for word in literaPointers:
                index = hNum.find(word)
                if index != 0:
                    hNum = hNum.replace(word, '')
            for word in buildingPointers:
                index = hNum.find(word)
                if index != 0:
                    hNum = hNum.replace(word, '+')                  # Указатель на строение будет заменён на +
            for word in corpsPointers:
                index = hNum.find(word)
                if index != 0 and index != len(hNum) - 1:
                    hNum = hNum.replace(word, '*')                  # Указатель на корпус будет заменён на *

            pattern = r'(\d+|[а-я]+|[+\-*/])'

            splitedHNum = re.findall(pattern, hNum)

            if len(splitedHNum) > 1:
                if splitedHNum[-1].isalpha():                           # Если последний символ - буква, то скорее всего прицепилась литера ("д1л"). Отправляем её в литеры
                    lit = splitedHNum[-1]
                    splitedHNum.pop(-1)
                indexEnd = len(splitedHNum)
                i = 0
                while i < indexEnd:                                     # Пока не достигли конца списка проверяем его элементы и ищем корпус, литеру, строение и т.д.
                    if i >= 0 and i <= len(splitedHNum):
                        if i == 0 and splitedHNum[i] == 'д':                # Удаляем слившуюся с номером дома букву д
                            splitedHNum, i, indexEnd = RemoveElement(splitedHNum, i, indexEnd)

                        if (splitedHNum[i] == '*' or splitedHNum[i] == 'к') and i > 0:      # Ищем слившийся корпус и отправляем его в нужное место                            
                            splitedHNum, i, indexEnd = RemoveElement(splitedHNum, i, indexEnd)
                            if i < len(splitedHNum) - 1:
                                cNum = splitedHNum[i + 1]
                                splitedHNum, i, indexEnd = RemoveElement(splitedHNum, i + 1, indexEnd)

                        if (splitedHNum[i] == '+' or splitedHNum[i] == 'с') and i > 0:      # Ищем слившееся строение и отправляем его в нужное место
                            bldNum = splitedHNum[i + 1]
                            splitedHNum, i, indexEnd = RemoveElement(splitedHNum, i, indexEnd)
                            if i < len(splitedHNum) - 1:
                                splitedHNum, i, indexEnd = RemoveElement(splitedHNum, i + 1, indexEnd)

                        if splitedHNum[i] == '/' and i > 0:                                  # Ищем дробь и выносим её в отдельный элемент                            
                            splitedHNum, i, indexEnd = RemoveElement(splitedHNum, i, indexEnd)
                            if i < len(splitedHNum) - 1:
                                slash = splitedHNum[i + 1]
                                splitedHNum, i, indexEnd = RemoveElement(splitedHNum, i + 1, indexEnd)

                        if splitedHNum[i] == '-' and i > 0:                                  # Иногда указывают литеру через символ "-" - тогда отправляем следующую букву в литеры, если она есть                            
                            splitedHNum, i, indexEnd = RemoveElement(splitedHNum, i, indexEnd)
                            if i < len(splitedHNum) - 1:
                                lit = splitedHNum[i + 1]
                                splitedHNum, i, indexEnd = RemoveElement(splitedHNum, i + 1, indexEnd)
                        elif splitedHNum[i] == '-':                                                               # Литера должна была раньше уйти куда надо, и если это так, то удаляем только тире
                            splitedHNum, i, indexEnd = RemoveElement(splitedHNum, i, indexEnd)

                    i += 1

            hNum = ''
            for word in splitedHNum:                                # И то, что осталось объединяем в номер дома
                hNum = ''.join([hNum, word])

            for char in hNum:
                if char.isdigit() == False and hNum.index(char) != 0 and currRecCount <= 5:
                    hNum, slash, cNum, lit, bldNum = tuple(SeparateHouseParts(hNum, slash, cNum, lit, bldNum, currRecCount))
                    break

            # endregion

            # region Старая версия

            # start = 0                                               
            # isLitera = 0
            # corpsStart = 0
            # slashIndex = -1
            # literaIsK = 0

            # for word in housePointers:                              # Если засосалась буква д ("д1", например), мы её уберём
            #     if word in hNum and word != 'д':
            #         hNum = hNum.replace(word, '')

            # if hNum[-1].isalpha():                                  # Если литера была написана слитно с домом, она скорее всего будет в конце. 
            #     isLitera = 1                                        # Поэтому если в конце номера не цифра - это скорее всего литера и мы считаем, что в адресе есть литера

            # index = hNum.find('лит')                                # Находим явный указатель на литеру, удаляем его из номера дома и отправляем литеру в литеры
            # if index != -1:
            #     index += 3
            #     lit = hNum[index]
            #     hNum = hNum.replace(hNum[index], '').replace('лит', '')

            # startSlash = 0
            # bldStart = 0
            # bldIndex = 0
            # i = 0
            
            # for char in hNum:                                               # И наконец чистим номер дома и определяем, есть ли у нас слеш в адресе ("2/1")
            #     if char.isdigit():                                          # Находим первую цифру. С неё будет идти поиск литеры (вариант "с123" - литеры нет)
            #         start = 1

            #     if char == 'с' and i < len(hNum) - 1 and i != 0:            # Нашли с - значит скорее всего прицепилось строение
            #         bldStart = 1
            #         bldIndex = i

            #     if char.isalpha() and start == 1 and isLitera == 1:
            #         lit = ''.join([lit, char])
            #         hNum = hNum.replace(char, '')
            #     elif char.isdigit() == False and char == 'к' and i != 0:
            #         corpsStart = 1
            #         hNum = hNum.replace(char, '')
                    
            #     if corpsStart == 1 and char.isdigit():
            #         cNum = ''.join([cNum, char])
            #         i -= 1
            #         if i < len(hNum) - 1:
            #             hNum = hNum[:i] + hNum[i+1:]     
            #         else:
            #             hNum = hNum[:i]     

            #     if char == '/':                                             # Если нашли слеш - запоминаем откуда начинаетсмя дробный номер и удаляем слеш
            #         startSlash = 1
            #         slashIndex = i
            #         hNum = hNum.replace(char, '')
            #         continue

            #     if startSlash == 1 and char.isdigit():
            #         hNum = hNum.replace(char, '')
            #         slash = ''.join([slash, char])

            #     if bldStart == 1 and char.isdigit():
            #         bldNum = ''.join([bldNum, char])

            #     if startSlash == 1 and char.isdigit() == False:
            #         startSlash = 0

            #     if slashIndex != -1:
            #         hNum = hNum[:slashIndex]

            #     if len(hNum) != 0 and hNum[0].isdigit() == False:
            #         hNum = hNum.replace(hNum[0], '')

            #     i += 1            

            # for char in cNum:                                               # Проверяем, не прицепилась ли литера к номеру корпуса ("д1 к 3л")
            #     if char.isdigit() == False and char != 'к':
            #         lit = ''.join([lit, char])
            #         cNum = cNum.replace(char, '')
            #     elif char.isdigit() == False:
            #         cNum = cNum.replace(char, '')

            # if bldStart == 1:                                               # Обрезаем номер дома до начала номера строения, если такое есть в адресе
            #     hNum = hNum[:bldIndex]

            # print(bldStart)

            # # if bldNum == hNum:
            # #     bldNum = ''

            # endregion

            return [hNum, slash, cNum, lit, bldNum]

        def RemoveBannedWords(tokens:list, bannedWords:list):              
        # Удалить "запрещённые" слова в адресе, которые мешают поиску. Слова берутся из словаря
            result = [item for item in tokens if item not in bannedWords]

            return result
        
        def RemoveSingleLetters(mainPart:list):                             
        # Удалить одиночные буквы в основной части адреса, если среди них нет цифры
            result = []

            for item in mainPart:
                banned = 0
                digitFound = 0
                if len(item) <= 2:
                    for char in item:
                        if char.isdigit():
                            digitFound = 1
                            break
                    if digitFound == 0:
                        banned = 1
                if banned == 0:
                    result.append(item)

            return result

        #region Словари
        #===Словари===
        # Указатели на регион
        areaPointers = {'область', 'обл', 'край', 'республика', 'респ'}

        # Указатели на город
        cityPointers = {'город', 'гор.', 'г'}
        
        # Особые указатели на "владения"
        properties = ['владение', 'вл', 'влд']

        # Указатели на корпус
        corpsPointers = ['корпус', 'корп', 'кор', 'к']

        # Указатели на литеры
        literaPointers = ['литера', 'литира', 'литер', 'литир', 'лит']

        # Указатели на строения
        buildingPointers = ['строение', 'стр', 'сооружение', 'соор', 'дробь']

        # Сокращения
        reductions = {'км':'километр', 'спб':'санкт-петербург', 'мск': 'москва', 'лин':'линия'}

        #=============
        #endregion

        # Веса токенов
        houseWeights = []                                                                               # Веса токенов, определяющие номер дома    
        corpseWeights = []                                                                              # Веса токенов, определяющие корпус    
        literaWeights = []                                                                              # Веса токенов, определяющие литеру    

        tokens = []                                                                                     # Список токенов после разбиения адреса на пробелы, запятые и точки

        mainAddress = []                                                                                # Основная часть адреса (регион, город, улица...)
        houseNumber = []                                                                                # Номер дома (номер, корпус, литера, строение, дробь...)

        # Промежуточные поля, в которые будет записываться результат разбиения номера дома
        hNum = ''                                                                                       # Основной номер
        cNum = ''                                                                                       # Номер корпуса
        slash = ''                                                                                      # То, что после дроби
        lit = ''                                                                                        # Литера
        bldNum = ''                                                                                     # Строение

        houseIndex = 0

        address = CleanAddress(address.lower())
        
        tokens = SplitAddressByTokens(address.lower(), totallyBannedWords, reductions)

        tokens = RemoveIndoor(tokens, indoorPointers)
        
        houseWeights, corpseWeights, literaWeights = GetBaseWeights(tokens)

        houseWeights, corpseWeights, literaWeights = ModifyWeightsByKeyWords(houseWeights, corpseWeights, literaWeights, 
                                                                            housePointers, corpsPointers, literaPointers)

        houseWeights, corpseWeights = ModifyWeightsPreciously(houseWeights, corpseWeights)

        houseWeights, corpseWeights, literaWeights = AdditionalWeightsModification(houseWeights, corpseWeights, literaWeights,
                                                                                streetPointers, corpsPointers, nonHouseMarkers,
                                                                                tokens)

        hNum, cNum, lit, bldNum, houseIndex = GetBestTokens(houseWeights, corpseWeights, literaWeights, buildingPointers, properties)

        if houseIndex != 0:
            tokens = tokens[:houseIndex]

        mainAddress = RemoveBannedWords(tokens, bannedWords)
        mainAddress = RemoveSingleLetters(mainAddress)
        houseNumber = SeparateHouseParts(hNum, slash, cNum, lit, bldNum, 0)        

        return [mainAddress, houseNumber]
    
    bannedWords = dicts[0]
    totallyBannedWords = dicts[1]
    streetPointers = dicts[2]
    housePointers = dicts[3]
    indoorPointers = dicts[4]
    nonHouseMarkers = dicts[5]
    
    result = GetAddressParts(address)

    return result

# BUG известные баги:
# 1+. число после "с" отправляется не в строение, а в корпус
# 2+. некоторые пермалинки с большим рейтингом не перезаписывают пермалинки с меньшим / точные совпадения не перекрывают частичные
# 3+. улица перед "30 лет", "9 мая", "32 октября" и т.п. ложно повышает вес токена
# 4+. номер дома в середине адреса парсится правильно, но надо сделать условие, что если номер дома не далее 3 токена, то мы исключаем из адреса не всю строку, а только токены с весами
# 5+. на данных №7 крашится
# 6+. Россия, Воронеж, улица 9 Января, 241/14 \\ 9 отправляется в дом. Добавить в слова, блокирующие изменения веса "января", "года" и т.п.
# 7+. "поселок" не вычищается
# 8+. "-й", "-ая", "-го", "-й", "-ий", "-ый", "-ой" и прочие штуки стоило бы вычищать. Если так сделать, надо будет обязательно проверить адреса "Россия, Краснодар, улица 1 Мая, 580", "Пермь, ул. 1-я Красноармейская, д.6"
# 9+. Очистить основу от скобок
# 10+. Если в обоих адресах нет номера дома, при сравнении должно возвращаться точное совпадение (1). Сейчас возвращается 0.

# TODO
# 1+. Проверить другие адреса из списка адресов к проверке.